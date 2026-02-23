"""Archive working files and wipe them after an edit session."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from editor.profile import (
    AIEDITED_PATH,
    EDITED_PATH,
    FINAL_PATH,
    HISTORY_DIR,
    ORIGINAL_PATH,
    read_file,
    wipe_file,
)


def archive_human_feedback() -> Path:
    """Archive original.md, edited.md, final.md, aiedited.md for a human feedback session.

    Returns the archive directory path.
    """
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    folder = HISTORY_DIR / f"{stamp}_human"
    folder.mkdir(parents=True, exist_ok=True)

    for src in [ORIGINAL_PATH, EDITED_PATH, FINAL_PATH, AIEDITED_PATH]:
        if src.exists() and read_file(src):
            shutil.copy2(src, folder / src.name)

    # Wipe working files (final.md stays for reference)
    wipe_file(ORIGINAL_PATH)
    wipe_file(EDITED_PATH)
    wipe_file(AIEDITED_PATH)

    return folder


def archive_ai_only() -> Path:
    """Archive original.md and final.md for an AI-only session.

    Returns the archive directory path.
    """
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    folder = HISTORY_DIR / f"{stamp}_ai"
    folder.mkdir(parents=True, exist_ok=True)

    for src in [ORIGINAL_PATH, FINAL_PATH]:
        if src.exists() and read_file(src):
            shutil.copy2(src, folder / src.name)

    # Wipe working files (final.md stays for reference)
    wipe_file(ORIGINAL_PATH)
    wipe_file(AIEDITED_PATH)

    return folder


def list_history() -> list[dict]:
    """List all archived edit sessions, newest first.

    Returns a list of dicts with 'name', 'mode', 'path', and 'files'.
    """
    if not HISTORY_DIR.exists():
        return []

    sessions = []
    for folder in sorted(HISTORY_DIR.iterdir(), reverse=True):
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        mode = "human" if folder.name.endswith("_human") else "ai"
        files = [f.name for f in folder.iterdir() if f.is_file()]

        sessions.append(
            {
                "name": folder.name,
                "mode": mode,
                "path": str(folder),
                "files": sorted(files),
            }
        )

    return sessions
