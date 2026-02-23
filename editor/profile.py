"""Simple file I/O for authorpreferences.md and working files."""

from __future__ import annotations

from pathlib import Path

# All paths relative to the repo root
ROOT = Path(__file__).resolve().parent.parent

ORIGINAL_PATH = ROOT / "original.md"
EDITED_PATH = ROOT / "edited.md"
AIEDITED_PATH = ROOT / "aiedited.md"
FINAL_PATH = ROOT / "final.md"
PREFERENCES_PATH = ROOT / "authorpreferences.md"
HISTORY_DIR = ROOT / "history"


def read_file(path: Path) -> str:
    """Read a file and return its stripped content. Returns '' if missing or empty."""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    return text


def write_file(path: Path, content: str) -> None:
    """Write content to a file, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def wipe_file(path: Path) -> None:
    """Clear a file's contents (write empty string)."""
    if path.exists():
        path.write_text("", encoding="utf-8")


def load_original() -> str:
    return read_file(ORIGINAL_PATH)


def load_feedback() -> str:
    return read_file(EDITED_PATH)


def load_preferences() -> str:
    return read_file(PREFERENCES_PATH)


def save_reasoning(content: str) -> None:
    write_file(AIEDITED_PATH, content)


def save_final(content: str) -> None:
    write_file(FINAL_PATH, content)


def save_preferences(content: str) -> None:
    write_file(PREFERENCES_PATH, content)


def reset_preferences() -> bool:
    """Delete authorpreferences.md. Returns True if file existed."""
    if PREFERENCES_PATH.exists():
        PREFERENCES_PATH.unlink()
        return True
    return False
