"""Tests for the archive/wipe logic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from editor import archive, profile


@pytest.fixture
def tmp_workspace(tmp_path: Path):
    """Set up a temp workspace with all working files."""
    paths = {
        "ORIGINAL_PATH": tmp_path / "original.md",
        "EDITED_PATH": tmp_path / "edited.md",
        "AIEDITED_PATH": tmp_path / "aiedited.md",
        "FINAL_PATH": tmp_path / "final.md",
        "PREFERENCES_PATH": tmp_path / "authorpreferences.md",
        "HISTORY_DIR": tmp_path / "history",
        "ROOT": tmp_path,
    }
    # Create the files with content
    paths["ORIGINAL_PATH"].write_text("Original chapter.", encoding="utf-8")
    paths["EDITED_PATH"].write_text("[too wordy]", encoding="utf-8")
    paths["AIEDITED_PATH"].write_text("reasoning here", encoding="utf-8")
    paths["FINAL_PATH"].write_text("Final chapter.", encoding="utf-8")
    (tmp_path / "history").mkdir()

    with patch.multiple("editor.profile", **paths):
        with patch.multiple("editor.archive", **{
            "ORIGINAL_PATH": paths["ORIGINAL_PATH"],
            "EDITED_PATH": paths["EDITED_PATH"],
            "AIEDITED_PATH": paths["AIEDITED_PATH"],
            "FINAL_PATH": paths["FINAL_PATH"],
            "HISTORY_DIR": paths["HISTORY_DIR"],
        }):
            yield paths


class TestArchiveHumanFeedback:
    def test_creates_archive_folder(self, tmp_workspace):
        folder = archive.archive_human_feedback()
        assert folder.exists()
        assert "_human" in folder.name

    def test_copies_all_four_files(self, tmp_workspace):
        folder = archive.archive_human_feedback()
        files = [f.name for f in folder.iterdir()]
        assert "original.md" in files
        assert "edited.md" in files
        assert "final.md" in files
        assert "aiedited.md" in files

    def test_wipes_original_edited_aiedited(self, tmp_workspace):
        archive.archive_human_feedback()
        assert tmp_workspace["ORIGINAL_PATH"].read_text(encoding="utf-8") == ""
        assert tmp_workspace["EDITED_PATH"].read_text(encoding="utf-8") == ""
        assert tmp_workspace["AIEDITED_PATH"].read_text(encoding="utf-8") == ""

    def test_final_not_wiped(self, tmp_workspace):
        archive.archive_human_feedback()
        # final.md keeps its content (stays for reference)
        assert tmp_workspace["FINAL_PATH"].read_text(encoding="utf-8") == "Final chapter."


class TestArchiveAiOnly:
    def test_creates_archive_folder(self, tmp_workspace):
        folder = archive.archive_ai_only()
        assert folder.exists()
        assert "_ai" in folder.name

    def test_copies_original_and_final(self, tmp_workspace):
        folder = archive.archive_ai_only()
        files = [f.name for f in folder.iterdir()]
        assert "original.md" in files
        assert "final.md" in files
        # edited.md should NOT be archived in AI mode
        assert "edited.md" not in files

    def test_wipes_original_and_aiedited(self, tmp_workspace):
        archive.archive_ai_only()
        assert tmp_workspace["ORIGINAL_PATH"].read_text(encoding="utf-8") == ""
        assert tmp_workspace["AIEDITED_PATH"].read_text(encoding="utf-8") == ""


class TestListHistory:
    def test_empty_history(self, tmp_workspace):
        sessions = archive.list_history()
        assert sessions == []

    def test_lists_sessions_newest_first(self, tmp_workspace):
        h = tmp_workspace["HISTORY_DIR"]
        (h / "2026-02-23_100000_human").mkdir()
        (h / "2026-02-23_100000_human" / "original.md").write_text("x", encoding="utf-8")
        (h / "2026-02-23_110000_ai").mkdir()
        (h / "2026-02-23_110000_ai" / "original.md").write_text("x", encoding="utf-8")

        sessions = archive.list_history()
        assert len(sessions) == 2
        assert sessions[0]["name"] == "2026-02-23_110000_ai"
        assert sessions[0]["mode"] == "ai"
        assert sessions[1]["mode"] == "human"

    def test_includes_file_list(self, tmp_workspace):
        h = tmp_workspace["HISTORY_DIR"]
        folder = h / "2026-01-01_120000_human"
        folder.mkdir()
        (folder / "original.md").write_text("x", encoding="utf-8")
        (folder / "final.md").write_text("x", encoding="utf-8")

        sessions = archive.list_history()
        assert "original.md" in sessions[0]["files"]
        assert "final.md" in sessions[0]["files"]
