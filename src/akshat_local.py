from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.core import AkshatCore, DB_PATH, HOST, PORT  # noqa: E402
from backend.runtime import EventBus, MemoryStore  # noqa: E402


def main() -> None:
    import uvicorn
    from akshat_fastapi import app

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
