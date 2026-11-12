"""Unit tests for the shared hook scripts."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from tools.hooks.check_large_files import oversized
from tools.hooks.dispatch import CURSOR_DENY_EXIT, handle
from tools.hooks.policy import (
    DEFAULT_MAX_BYTES,
    GOLD_MAX_BYTES,
    OWNER_EDIT_DENIAL,
    claude_stop_body,
    commit_message_error,
    cursor_stop_body,
    denied_push,
    denied_shell_reason,
    is_owner_only,
)
from tools.hooks.ruff_lint import ruff_check_command

from qecbench.repo import repo_root

_ROOT = repo_root()


def test_owner_paths() -> None:
    assert is_owner_only("spec/SCIENCE.md")
    assert is_owner_only("/workspace/spec/SCIENCE.md")
    assert is_owner_only("data/gold/values.csv")
    assert is_owner_only("/tmp/repo/data/gold/values.csv")
    assert not is_owner_only("src/qecbench/reference/smoke.py")
    assert not is_owner_only("data/other/file.csv")
    assert not is_owner_only("specs/notes.md")


@pytest.mark.parametrize(
    ("command", "denied"),
    [
        ("git push --force", True),
        ("git push --force-with-lease origin feature", True),
        ("git push -f origin feature", True),
        ("git push origin feature", False),
        ("git push origin main", True),
        ("git push -u origin main", True),
        ("git push origin maintenance", False),
        ("git commit --no-verify -m 'chore(tooling): x'", True),
        ("git commit -n -m 'chore(tooling): x'", True),
        ("git commit -m 'chore(tooling): x'", False),
        ("git reset --hard main", True),
        ("git reset --hard origin/main", True),
        ("git reset --hard refs/heads/main", True),
        ("git reset --hard HEAD~1", False),
        ("OWNER_SPEC_EDIT=1 git status", True),
        ("pip install numpy", True),
        ("pip3 install numpy", True),
        ("python -m pip install numpy", True),
        ("python3 -m pip install numpy", True),
        ("uv add numpy", False),
        ("uv pip install numpy", True),
    ],
)
def test_shell_denials(command: str, denied: bool) -> None:
    reason = denied_shell_reason(command)
    assert (reason is not None) is denied


def test_cursor_and_claude_shell_hooks_agree() -> None:
    command = "git push --force origin feature"
    cursor_code, cursor_body = handle(
        {"hook_event_name": "beforeShellExecution", "command": command}
    )
    claude_code, claude_body = handle(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }
    )
    assert cursor_code == CURSOR_DENY_EXIT
    assert cursor_body["permission"] == "deny"
    assert "force" in str(cursor_body["agent_message"])
    assert claude_code == 0
    inner = claude_body["hookSpecificOutput"]
    assert isinstance(inner, dict)
    assert inner["permissionDecision"] == "deny"


def test_cursor_allows_ordinary_push() -> None:
    code, body = handle(
        {
            "hook_event_name": "beforeShellExecution",
            "command": "git push -u origin cursor/m0_scaffold",
        }
    )
    assert code == 0
    assert body == {"permission": "allow"}


def test_reads_of_spec_are_allowed_and_edits_are_denied() -> None:
    code, body = handle({"hook_event_name": "beforeReadFile", "file_path": "/repo/spec/SCIENCE.md"})
    assert code == 0
    assert body == {"permission": "allow"}
    code, body = handle(
        {
            "hook_event_name": "preToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/repo/spec/SCIENCE.md"},
        }
    )
    assert code == CURSOR_DENY_EXIT
    assert body["permission"] == "deny"
    assert "needs-science-decision" in str(body["agent_message"])
    code, body = handle(
        {"hook_event_name": "afterFileEdit", "file_path": "/repo/spec/TOLERANCES.md"}
    )
    assert code == CURSOR_DENY_EXIT
    assert body["permission"] == "deny"


def test_claude_edit_denial_matches_cursor() -> None:
    code, body = handle(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "data/gold/values.csv"},
        }
    )
    assert code == 0
    inner = body["hookSpecificOutput"]
    assert isinstance(inner, dict)
    assert inner["permissionDecision"] == "deny"
    assert inner["permissionDecisionReason"] == OWNER_EDIT_DENIAL
    code, body = handle(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "spec/SOURCES.md"},
        }
    )
    assert body["decision"] == "block"


def test_after_file_edit_formats_python(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    path.write_text("def hello( ):\n    x=1\n    return x\n", encoding="utf-8")
    code, body = handle({"hook_event_name": "afterFileEdit", "file_path": str(path)})
    assert code == 0
    assert body == {}
    assert "x = 1" in path.read_text(encoding="utf-8")


def test_commit_messages() -> None:
    assert commit_message_error("chore(tooling): M0 scaffold\n") is None
    assert commit_message_error("feat(task): add example_000_smoke\n") is None
    assert commit_message_error("update stuff\n") is not None
    assert commit_message_error("chore: missing scope\n") is not None
    assert commit_message_error("chore(physics): invented\n") is not None
    trailer = "chore(tooling): M0 scaffold\n\nCo-authored-by: Bot <bot@example.com>\n"
    assert commit_message_error(trailer) is not None
    generated = "chore(tooling): M0 scaffold\n\nGenerated-by: tool\n"
    assert commit_message_error(generated) is not None
    made_with = "chore(tooling): M0 scaffold\n\nmade with cursor\n"
    assert commit_message_error(made_with) is not None


def test_commit_msg_script(tmp_path: Path) -> None:
    good = tmp_path / "good.txt"
    good.write_text("chore(tooling): M0 scaffold\n", encoding="utf-8")
    bad = tmp_path / "bad.txt"
    bad.write_text("not conventional\n", encoding="utf-8")
    script = _ROOT / "tools" / "hooks" / "check_commit_msg.py"
    passed = subprocess.run([sys.executable, str(script), str(good)], check=False)
    failed = subprocess.run(
        [sys.executable, str(script), str(bad)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert passed.returncode == 0
    assert failed.returncode == 1
    assert "Conventional Commits" in failed.stderr


def test_push_destination() -> None:
    refusal = "refs/heads/cursor/m0_scaffold abc refs/heads/main def\n"
    allowed = "refs/heads/cursor/m0_scaffold abc refs/heads/cursor/m0_scaffold def\n"
    assert denied_push(refusal, "cursor/m0_scaffold") is not None
    assert denied_push(allowed, "cursor/m0_scaffold") is None
    assert denied_push("", "main") is not None
    assert denied_push("", "cursor/m0_scaffold") is None
    script = _ROOT / "tools" / "hooks" / "deny_push_main.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=refusal,
        text=True,
        capture_output=True,
        cwd=_ROOT,
        check=False,
    )
    assert proc.returncode == 1
    assert "push to main is refused" in proc.stderr


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)


def test_large_file_policy(tmp_path: Path) -> None:
    _git_init(tmp_path)
    gold = tmp_path / "data" / "gold"
    gold.mkdir(parents=True)
    small = tmp_path / "notes.txt"
    small.write_text("ok\n", encoding="utf-8")
    over_default = tmp_path / "blob.bin"
    over_default.write_bytes(b"a" * (DEFAULT_MAX_BYTES + 1))
    gold_ok = gold / "table.bin"
    gold_ok.write_bytes(b"b" * (DEFAULT_MAX_BYTES + 1))
    subprocess.run(
        ["git", "add", "notes.txt", "blob.bin", "data/gold/table.bin"],
        cwd=tmp_path,
        check=True,
    )
    script = _ROOT / "tools" / "hooks" / "check_large_files.py"
    failed = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode == 1
    assert "blob.bin" in failed.stderr
    assert "table.bin" not in failed.stderr
    subprocess.run(
        ["git", "rm", "--cached", "blob.bin"], cwd=tmp_path, check=True, capture_output=True
    )
    passed = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert passed.returncode == 0
    huge = gold / "huge.bin"
    huge.write_bytes(b"c" * (GOLD_MAX_BYTES + 1))
    subprocess.run(["git", "add", "data/gold/huge.bin"], cwd=tmp_path, check=True)
    too_big = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert too_big.returncode == 1
    assert "huge.bin" in too_big.stderr


def test_oversized_helper() -> None:
    assert oversized([("src/a.py", DEFAULT_MAX_BYTES)]) == []
    assert oversized([("src/a.py", DEFAULT_MAX_BYTES + 1)]) != []


def test_spec_untouched_hook(tmp_path: Path) -> None:
    _git_init(tmp_path)
    spec = tmp_path / "spec"
    spec.mkdir()
    target = spec / "SCIENCE.md"
    target.write_text("# Science\n\n## Scope\n\nTODO(owner)\n", encoding="utf-8")
    subprocess.run(["git", "add", "spec/SCIENCE.md"], cwd=tmp_path, check=True)
    script = _ROOT / "tools" / "check_spec_untouched.py"
    blocked = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        env={key: value for key, value in os.environ.items() if key != "OWNER_SPEC_EDIT"},
    )
    assert blocked.returncode == 1
    assert "needs-science-decision" in blocked.stderr
    assert "spec/SCIENCE.md" in blocked.stderr
    allowed_env = os.environ.copy()
    allowed_env["OWNER_SPEC_EDIT"] = "1"
    allowed = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        check=False,
        env=allowed_env,
    )
    assert allowed.returncode == 0
    still_blocked = os.environ.copy()
    still_blocked["OWNER_SPEC_EDIT"] = "0"
    rejected = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        check=False,
        env=still_blocked,
    )
    assert rejected.returncode == 1


def _run_dispatch(
    payload: dict[str, object], env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_ROOT / "tools" / "hooks" / "dispatch.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        cwd=_ROOT,
        check=False,
    )


def _make_on_path(tmp_path: Path, body: str) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(parents=True)
    make = bindir / "make"
    make.write_text(body, encoding="utf-8")
    make.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
    return env


def test_stop_hooks_follow_make_check(tmp_path: Path) -> None:
    failing = _make_on_path(tmp_path / "fail", "#!/bin/sh\necho check-failed\nexit 1\n")
    cursor = _run_dispatch({"hook_event_name": "stop", "status": "completed"}, failing)
    assert cursor.returncode == 0
    cursor_body = json.loads(cursor.stdout)
    assert "keep working" in cursor_body["followup_message"].lower()
    assert "check-failed" in cursor_body["followup_message"]
    claude = _run_dispatch({"hook_event_name": "Stop"}, failing)
    claude_body = json.loads(claude.stdout)
    assert claude_body["decision"] == "block"
    assert "keep working" in claude_body["reason"].lower()
    passing = _make_on_path(tmp_path / "pass", "#!/bin/sh\nexit 0\n")
    allowed = _run_dispatch({"hook_event_name": "stop", "status": "completed"}, passing)
    assert json.loads(allowed.stdout) == {}
    aborted = _run_dispatch(
        {"hook_event_name": "stop", "status": "aborted"},
        _make_on_path(tmp_path / "abort", "#!/bin/sh\necho should-not-run\nexit 1\n"),
    )
    assert json.loads(aborted.stdout) == {}
    assert "should-not-run" not in aborted.stderr


def test_stop_bodies() -> None:
    assert cursor_stop_body(0, "ok") == {}
    assert "keep working" in cursor_stop_body(1, "boom")["followup_message"].lower()
    assert claude_stop_body(0, "ok") == {}
    assert claude_stop_body(1, "boom")["decision"] == "block"


def test_ruff_lint_ci_mode() -> None:
    local = ruff_check_command(["src/qecbench/repo.py"], ci=False)
    ci = ruff_check_command(["src/qecbench/repo.py"], ci=True)
    assert "--fix" in local
    assert "--fix" not in ci


def test_hook_configs_share_dispatch() -> None:
    cursor = json.loads((_ROOT / ".cursor" / "hooks.json").read_text(encoding="utf-8"))
    claude = json.loads((_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    cursor_commands = [hook["command"] for hooks in cursor["hooks"].values() for hook in hooks]
    assert cursor_commands
    assert all(command == "python3 tools/hooks/dispatch.py" for command in cursor_commands)
    claude_commands = [
        hook["command"]
        for groups in claude["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]
    assert claude_commands
    assert all(command == "python3 tools/hooks/dispatch.py" for command in claude_commands)
