#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${TASK_OUTPUT_DIR:-}" ]]; then
  echo "TASK_OUTPUT_DIR is not set" >&2
  exit 1
fi
python - <<'PY'
import json
import os
from pathlib import Path

from qecbench.reference.smoke import payload

destination = Path(os.environ["TASK_OUTPUT_DIR"]) / "output.json"
destination.write_text(json.dumps(payload()), encoding="utf-8")
PY
