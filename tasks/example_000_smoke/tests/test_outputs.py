"""Hidden verifier for the format demo.

The expected object comes from the reference payload. It is not a tolerance
and not a physical observable. See docs/adr/0002-task-format.md.
"""

import json
import os
from pathlib import Path

from qecbench.reference.smoke import payload


def test_output_matches_format_demo_payload() -> None:
    path = Path(os.environ["TASK_OUTPUT_DIR"]) / "output.json"
    observed = json.loads(path.read_text(encoding="utf-8"))
    assert observed == payload()
