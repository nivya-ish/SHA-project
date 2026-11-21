from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure backend package importable when running from project root or backend dir
BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
for p in (str(BACKEND_ROOT), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Helpful default env for tests
os.environ.setdefault("GEMINI_ENABLED", "false")
