from __future__ import annotations

from pathlib import Path
from typing import List


def list_workspace_files(root: Path, limit: int = 200) -> List[str]:
    files: List[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts:
            files.append(str(path.relative_to(root)))
        if len(files) >= limit:
            break
    return files
