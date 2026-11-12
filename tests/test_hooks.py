"""Unit tests for git hooks and the shared Cursor / Claude Code hook scripts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.check_spec_untouched import owner_staged
from tools.hooks.after_file_edit import format_python, response, revert_owner_edit
from tools.hooks.commit_msg import commit_message_error
from tools.hooks.common import is_owner_only
from tools.hooks.guard_edit import decision
from tools.hooks.pre_push import refuses_push
from tools.hooks.shell_guard import shell_denial
from tools.hooks.stop import stop_response

ROOT = Path(__file__).resolve().parents[1]


def _run_module(module: str, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", module],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )


def test_shell_denial_list() -> None:
    denied = [
        "git push --force",
        "git push --force-with-lease origin feature",
        "git push -f origin HEAD",
        "git push origin main",
        "git push origin HEAD:main",
        "git commit --no-verify -m 'feat(task): x'",
        "git commit -n -m 'feat(task): x'",
        "OWNER_SPEC_EDIT=1 git commit -m 'chore(spec): x'",
        "pip install stim",
        "pip3 install stim",
        "python -m pip install numpy",
        "python3 -m pip install numpy",
        "uv pip install stim",
        "git reset --hard origin/main",
        "git reset --hard main",
    ]
    for command in denied:
        assert shell_denial(command, current_branch="cursor/m0-scaffold") is not None, command
    assert shell_denial("git reset --hard", current_branch="main") is not None
    allowed = [
        "uv add stim",
        "git push -u origin cursor/m0-scaffold",
        "git status",
        "git reset --hard HEAD~1",
        "make check",
    ]
    for command in allowed:
        assert shell_denial(command, current_branch="cursor/m0-scaffold") is None, command


def test_before_shell_cursor_and_claude_payloads() -> None:
    denied = _run_module(
        "tools.hooks.before_shell",
        {"command": "git push --force", "cwd": str(ROOT)},
    )
    assert denied.returncode == 0
    assert json.loads(denied.stdout)["permission"] == "deny"
    allowed = _run_module(
        "tools.hooks.before_shell",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        },
    )
    assert allowed.returncode == 0
    body = json.loads(allowed.stdout)
    assert body["hookSpecificOutput"]["permissionDecision"] == "allow"


def test_before_read_allows_spec() -> None:
    result = _run_module(
        "tools.hooks.before_read_file",
        {"file_path": str(ROOT / "spec" / "SCIENCE.md")},
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["permission"] == "allow"


def test_guard_edit_denies_spec_and_allows_src() -> None:
    spec = str(ROOT / "spec" / "SCIENCE.md")
    denied = decision(spec, root=ROOT, claude=True)
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "needs-science-decision" in denied["hookSpecificOutput"]["permissionDecisionReason"]
    allowed = decision(str(ROOT / "src" / "qecbench" / "__init__.py"), root=ROOT, claude=False)
    assert allowed["permission"] == "allow"
    no_path = decision(None, root=ROOT, claude=False)
    assert no_path["permission"] == "allow"


def test_guard_edit_cli_does_not_change_spec() -> None:
    spec = ROOT / "spec" / "SCIENCE.md"
    before = spec.read_text(encoding="utf-8")
    result = _run_module(
        "tools.hooks.guard_edit",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": str(spec)},
        },
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert spec.read_text(encoding="utf-8") == before


def test_owner_path_detection(tmp_path: Path) -> None:
    assert is_owner_only(tmp_path / "spec" / "SCIENCE.md", root=tmp_path)
    assert is_owner_only(tmp_path / "data" / "gold" / "values.csv", root=tmp_path)
    assert not is_owner_only(tmp_path / "src" / "qecbench" / "__init__.py", root=tmp_path)
    assert not is_owner_only(tmp_path / "outside.py", root=tmp_path / "repo")
    assert owner_staged(["spec/SCIENCE.md", "src/qecbench/__init__.py"]) == ["spec/SCIENCE.md"]
    assert owner_staged(["data/gold/values.csv"]) == ["data/gold/values.csv"]
    assert owner_staged(["README.md"]) == []


def test_revert_owner_edit(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    spec = tmp_path / "spec"
    spec.mkdir()
    tracked = spec / "SCIENCE.md"
    tracked.write_text("original\n", encoding="utf-8")
    subprocess.run(["git", "add", "spec/SCIENCE.md"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=test",
            "commit",
            "-m",
            "init",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    tracked.write_text("edited\n", encoding="utf-8")
    revert_owner_edit(tracked, root=tmp_path)
    assert tracked.read_text(encoding="utf-8") == "original\n"
    fresh = spec / "NEW.md"
    fresh.write_text("new\n", encoding="utf-8")
    revert_owner_edit(fresh, root=tmp_path)
    assert not fresh.exists()


def test_format_python(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("x=1\n", encoding="utf-8")
    format_python(target)
    assert target.read_text(encoding="utf-8") == "x = 1\n"
    note = tmp_path / "note.md"
    note.write_text("x=1\n", encoding="utf-8")
    format_python(note)
    assert note.read_text(encoding="utf-8") == "x=1\n"


def test_after_file_edit_response() -> None:
    assert response(denied=False, claude=False) == {}
    blocked = response(denied=True, claude=True)
    assert blocked["decision"] == "block"
    assert "needs-science-decision" in blocked["reason"]


def test_commit_messages(tmp_path: Path) -> None:
    assert commit_message_error("feat(task): add decoding-001-repetition-memory") is None
    assert commit_message_error("chore(tooling): M0 scaffold") is None
    assert commit_message_error("feat(task)!: break the format\n\nbody\n") is None
    assert commit_message_error("added stuff") is not None
    assert commit_message_error("feat: missing scope") is not None
    assert commit_message_error("feat(nope): bad scope") is not None
    assert commit_message_error("Merge branch 'main'") is not None
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text("added stuff\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "tools.hooks.commit_msg", str(message)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1


def test_refuses_push_to_main() -> None:
    assert refuses_push("", "main") is not None
    feature = "refs/heads/cursor/m0-scaffold aaa refs/heads/main bbb\n"
    assert refuses_push(feature, "cursor/m0-scaffold") is not None
    other = "refs/heads/cursor/m0-scaffold aaa refs/heads/cursor/m0-scaffold bbb\n"
    assert refuses_push(other, "cursor/m0-scaffold") is None
    assert refuses_push("", "cursor/m0-scaffold", remote_branch="refs/heads/main") is not None
    assert (
        refuses_push(
            "",
            "cursor/m0-scaffold",
            remote_branch="refs/heads/cursor/m0-scaffold",
        )
        is None
    )
    with pytest.raises(SystemExit):
        refuses_push("not-a-ref-line\n", "cursor/m0-scaffold")


def test_pre_push_script_refuses_pre_commit_remote_branch() -> None:
    """pre-commit leaves stdin empty and sets PRE_COMMIT_REMOTE_BRANCH."""
    env = os.environ.copy()
    env["PRE_COMMIT_REMOTE_BRANCH"] = "refs/heads/main"
    result = subprocess.run(
        [sys.executable, "-m", "tools.hooks.pre_push"],
        input="",
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )
    assert result.returncode == 1
    assert "push to main is refused" in result.stderr
    assert "pytest" not in result.stdout


def test_pre_commit_hook_impl_refuses_push_to_main() -> None:
    """The managed pre-push hook must refuse main without running make check."""
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    stdin = f"refs/heads/cursor/m0-scaffold {sha} refs/heads/main {sha}\n"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pre_commit",
            "hook-impl",
            "--config=.pre-commit-config.yaml",
            "--hook-type=pre-push",
            "--hook-dir",
            str(ROOT / ".git" / "hooks"),
            "--",
            "origin",
            "https://example.invalid/qec-bench.git",
        ],
        input=stdin,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "push to main is refused" in combined
    assert "passed in" not in combined


def test_stop_response() -> None:
    assert stop_response("ok", returncode=0, claude=False) == {}
    cursor = stop_response("line\nboom", returncode=1, claude=False)
    assert "make check failed" in cursor["followup_message"]
    claude = stop_response("boom", returncode=2, claude=True)
    assert claude["decision"] == "block"


def test_check_spec_untouched_script(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    spec = tmp_path / "spec"
    spec.mkdir()
    (spec / "SCIENCE.md").write_text("# Science\n", encoding="utf-8")
    subprocess.run(["git", "add", "spec/SCIENCE.md"], cwd=tmp_path, check=True)
    env = os.environ.copy()
    env.pop("OWNER_SPEC_EDIT", None)
    blocked = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_spec_untouched.py")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert blocked.returncode == 1
    assert "owner-only" in blocked.stderr
    env["OWNER_SPEC_EDIT"] = "1"
    allowed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_spec_untouched.py")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert allowed.returncode == 0
