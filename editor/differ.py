"""Paragraph-level diffing between original and edited markdown files."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Edit:
    """A single detected edit between original and edited text."""

    original_text: str
    edited_text: str
    paragraph_index: int
    diff_summary: str
    edit_type: str = ""  # filled by analyzer


def split_paragraphs(text: str) -> list[str]:
    """Split markdown text into paragraphs on double-newline boundaries.

    Preserves UI blocks (lines starting with [) grouped with surrounding prose.
    Strips leading/trailing whitespace from each paragraph but keeps internal
    formatting intact.
    """
    raw = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in raw if p.strip()]


def make_diff_summary(original: str, edited: str) -> str:
    """Build a human-readable unified diff summary between two paragraph strings."""
    orig_lines = original.splitlines(keepends=True)
    edit_lines = edited.splitlines(keepends=True)
    diff = difflib.unified_diff(orig_lines, edit_lines, lineterm="")
    # Skip the --- / +++ header lines, keep only content hunks
    lines = []
    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines)


def diff_paragraphs(original_text: str, edited_text: str) -> list[Edit]:
    """Compare two markdown documents paragraph-by-paragraph and return Edits.

    Uses SequenceMatcher to align paragraphs so insertions, deletions, and
    replacements are all captured with correct paragraph indices.
    """
    orig_paras = split_paragraphs(original_text)
    edit_paras = split_paragraphs(edited_text)

    matcher = difflib.SequenceMatcher(None, orig_paras, edit_paras)
    edits: list[Edit] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        if tag == "replace":
            # Pair up replaced paragraphs 1:1 where possible
            orig_chunk = orig_paras[i1:i2]
            edit_chunk = edit_paras[j1:j2]
            pairs = max(len(orig_chunk), len(edit_chunk))
            for k in range(pairs):
                o = orig_chunk[k] if k < len(orig_chunk) else ""
                e = edit_chunk[k] if k < len(edit_chunk) else ""
                edits.append(
                    Edit(
                        original_text=o,
                        edited_text=e,
                        paragraph_index=i1 + k,
                        diff_summary=make_diff_summary(o, e),
                    )
                )

        elif tag == "delete":
            for k, idx in enumerate(range(i1, i2)):
                edits.append(
                    Edit(
                        original_text=orig_paras[idx],
                        edited_text="",
                        paragraph_index=idx,
                        diff_summary=f"- [DELETED paragraph]",
                    )
                )

        elif tag == "insert":
            for k, idx in enumerate(range(j1, j2)):
                edits.append(
                    Edit(
                        original_text="",
                        edited_text=edit_paras[idx],
                        paragraph_index=i1 + k,
                        diff_summary=f"+ [INSERTED paragraph]",
                    )
                )

    return edits


def diff_files(original_path: str | Path, edited_path: str | Path) -> list[Edit]:
    """Read two markdown files from disk and return their paragraph-level diffs."""
    original = Path(original_path).read_text(encoding="utf-8")
    edited = Path(edited_path).read_text(encoding="utf-8")
    return diff_paragraphs(original, edited)
