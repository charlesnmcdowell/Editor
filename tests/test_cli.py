"""Tests for the Stage 2 Click CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from editor.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestEditCommand:
    @patch("editor.cli.load_original")
    def test_empty_original_errors(self, mock_load, runner):
        mock_load.return_value = ""
        result = runner.invoke(cli, ["edit"])
        assert result.exit_code != 0
        assert "empty" in result.output.lower()

    @patch("editor.cli.archive_ai_only")
    @patch("editor.cli.save_final")
    @patch("editor.cli.save_reasoning")
    @patch("editor.cli.edit_ai_only")
    @patch("editor.cli.load_preferences")
    @patch("editor.cli.load_feedback")
    @patch("editor.cli.load_original")
    def test_ai_only_mode(
        self, mock_orig, mock_fb, mock_prefs, mock_edit, mock_save_r, mock_save_f, mock_archive, runner
    ):
        mock_orig.return_value = "Chapter text."
        mock_fb.return_value = ""
        mock_prefs.return_value = "Be concise."
        mock_edit.return_value = ("AI reasoning.", "Edited chapter.")
        mock_archive.return_value = Path("/tmp/history/2026-01-01_ai")

        result = runner.invoke(cli, ["edit"])
        assert result.exit_code == 0
        assert "AI-ONLY MODE" in result.output
        assert "Skipping preference update" in result.output
        mock_edit.assert_called_once()
        mock_archive.assert_called_once()

    @patch("editor.cli.archive_human_feedback")
    @patch("editor.cli.save_preferences")
    @patch("editor.cli.update_preferences")
    @patch("editor.cli.save_final")
    @patch("editor.cli.save_reasoning")
    @patch("editor.cli.edit_with_feedback")
    @patch("editor.cli.load_preferences")
    @patch("editor.cli.load_feedback")
    @patch("editor.cli.load_original")
    def test_human_feedback_mode(
        self,
        mock_orig, mock_fb, mock_prefs, mock_edit, mock_save_r, mock_save_f,
        mock_update_prefs, mock_save_prefs, mock_archive, runner
    ):
        mock_orig.return_value = "Chapter text."
        mock_fb.return_value = "[too wordy]"
        mock_prefs.return_value = ""
        mock_edit.return_value = ("Reasoning.", "Edited chapter.")
        mock_update_prefs.return_value = "# Preferences\n- Be concise."
        mock_archive.return_value = Path("/tmp/history/2026-01-01_human")

        result = runner.invoke(cli, ["edit"])
        assert result.exit_code == 0
        assert "HUMAN FEEDBACK MODE" in result.output
        assert "Extracting style preferences" in result.output
        mock_edit.assert_called_once()
        mock_update_prefs.assert_called_once()
        mock_save_prefs.assert_called_once()
        mock_archive.assert_called_once()


class TestPreferencesCommand:
    @patch("editor.cli.load_preferences")
    def test_no_prefs(self, mock_prefs, runner):
        mock_prefs.return_value = ""
        result = runner.invoke(cli, ["preferences"])
        assert result.exit_code == 0
        assert "No preferences" in result.output

    @patch("editor.cli.load_preferences")
    def test_shows_prefs(self, mock_prefs, runner):
        mock_prefs.return_value = "# Preferences\n- Be concise."
        result = runner.invoke(cli, ["preferences"])
        assert result.exit_code == 0
        assert "Be concise" in result.output


class TestHistoryCommand:
    @patch("editor.cli.list_history")
    def test_no_history(self, mock_hist, runner):
        mock_hist.return_value = []
        result = runner.invoke(cli, ["history"])
        assert result.exit_code == 0
        assert "No archived" in result.output

    @patch("editor.cli.list_history")
    def test_lists_sessions(self, mock_hist, runner):
        mock_hist.return_value = [
            {
                "name": "2026-02-23_143022_human",
                "mode": "human",
                "path": "/tmp/history/2026-02-23_143022_human",
                "files": ["original.md", "edited.md", "final.md"],
            }
        ]
        result = runner.invoke(cli, ["history"])
        assert result.exit_code == 0
        assert "2026-02-23_143022_human" in result.output
        assert "Human Feedback" in result.output


class TestResetCommand:
    @patch("editor.cli.reset_preferences")
    def test_reset_confirmed(self, mock_reset, runner):
        mock_reset.return_value = True
        result = runner.invoke(cli, ["reset", "--yes"])
        assert result.exit_code == 0
        assert "deleted" in result.output

    @patch("editor.cli.reset_preferences")
    def test_reset_aborted(self, mock_reset, runner):
        mock_reset.return_value = False
        result = runner.invoke(cli, ["reset"], input="n\n")
        assert result.exit_code != 0 or "Aborted" in result.output
        mock_reset.assert_not_called()
