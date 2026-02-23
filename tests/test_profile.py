"""Tests for the Stage 2 profile module — file I/O for working files."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from editor import profile


@pytest.fixture
def tmp_files(tmp_path: Path):
    """Patch all file paths to use a temp directory."""
    paths = {
        "ORIGINAL_PATH": tmp_path / "original.md",
        "EDITED_PATH": tmp_path / "edited.md",
        "AIEDITED_PATH": tmp_path / "aiedited.md",
        "FINAL_PATH": tmp_path / "final.md",
        "PREFERENCES_PATH": tmp_path / "authorpreferences.md",
        "HISTORY_DIR": tmp_path / "history",
        "ROOT": tmp_path,
    }
    with patch.multiple("editor.profile", **paths):
        yield paths


class TestReadWriteFile:
    def test_read_missing_returns_empty(self, tmp_path: Path):
        assert profile.read_file(tmp_path / "nope.md") == ""

    def test_read_empty_file_returns_empty(self, tmp_path: Path):
        f = tmp_path / "empty.md"
        f.write_text("", encoding="utf-8")
        assert profile.read_file(f) == ""

    def test_read_whitespace_only_returns_empty(self, tmp_path: Path):
        f = tmp_path / "ws.md"
        f.write_text("   \n  \n  ", encoding="utf-8")
        assert profile.read_file(f) == ""

    def test_write_and_read_roundtrip(self, tmp_path: Path):
        f = tmp_path / "test.md"
        profile.write_file(f, "Hello world")
        assert profile.read_file(f) == "Hello world"

    def test_write_creates_parent_dirs(self, tmp_path: Path):
        f = tmp_path / "a" / "b" / "test.md"
        profile.write_file(f, "deep")
        assert f.exists()

    def test_wipe_clears_content(self, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("content", encoding="utf-8")
        profile.wipe_file(f)
        assert f.read_text(encoding="utf-8") == ""

    def test_wipe_missing_file_no_error(self, tmp_path: Path):
        profile.wipe_file(tmp_path / "nope.md")  # should not raise


class TestLoadHelpers:
    def test_load_original(self, tmp_files):
        tmp_files["ORIGINAL_PATH"].write_text("chapter text", encoding="utf-8")
        assert profile.load_original() == "chapter text"

    def test_load_feedback_empty(self, tmp_files):
        assert profile.load_feedback() == ""

    def test_load_preferences_missing(self, tmp_files):
        assert profile.load_preferences() == ""


class TestSaveHelpers:
    def test_save_reasoning(self, tmp_files):
        profile.save_reasoning("reasoning content")
        assert tmp_files["AIEDITED_PATH"].read_text(encoding="utf-8") == "reasoning content"

    def test_save_final(self, tmp_files):
        profile.save_final("final chapter")
        assert tmp_files["FINAL_PATH"].read_text(encoding="utf-8") == "final chapter"

    def test_save_preferences(self, tmp_files):
        profile.save_preferences("prefs text")
        assert tmp_files["PREFERENCES_PATH"].read_text(encoding="utf-8") == "prefs text"


class TestResetPreferences:
    def test_reset_deletes_file(self, tmp_files):
        tmp_files["PREFERENCES_PATH"].write_text("prefs", encoding="utf-8")
        assert profile.reset_preferences() is True
        assert not tmp_files["PREFERENCES_PATH"].exists()

    def test_reset_missing_returns_false(self, tmp_files):
        assert profile.reset_preferences() is False
