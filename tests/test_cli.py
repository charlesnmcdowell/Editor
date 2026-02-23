"""Tests for the Click CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from editor.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_profile(tmp_path: Path):
    return tmp_path / "style_profile.json"


class TestLearnCommand:
    def test_no_diffs_reports_clean(self, runner: CliRunner, tmp_path: Path):
        # Two identical files
        f = tmp_path / "same.md"
        f.write_text("Hello world.\n\nSecond paragraph.", encoding="utf-8")
        result = runner.invoke(cli, ["learn", str(f), str(f)])
        assert result.exit_code == 0
        assert "No differences" in result.output

    @patch("editor.cli.analyze_edits")
    @patch("editor.cli.save_profile")
    @patch("editor.cli.load_profile")
    def test_learn_pipeline_runs(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
        mock_analyze: MagicMock,
        runner: CliRunner,
    ):
        mock_load.return_value = {"rules": [], "chapters_analyzed": 0}
        mock_analyze.return_value = [
            {
                "paragraph_index": 0,
                "patterns": [
                    {
                        "category": "prose_tightening",
                        "rule": "Cut filter words",
                        "confidence": 0.9,
                        "example_before": "x",
                        "example_after": "y",
                    }
                ],
            }
        ]

        orig = str(FIXTURES / "original.md")
        edit = str(FIXTURES / "edited.md")
        result = runner.invoke(cli, ["learn", orig, edit])

        assert result.exit_code == 0
        assert "pattern(s)" in result.output
        assert "Profile updated" in result.output
        mock_analyze.assert_called_once()
        mock_save.assert_called_once()

    def test_learn_missing_file(self, runner: CliRunner):
        result = runner.invoke(cli, ["learn", "nonexistent.md", "also_missing.md"])
        assert result.exit_code != 0


class TestProfileCommand:
    @patch("editor.cli.load_profile")
    def test_empty_profile(self, mock_load: MagicMock, runner: CliRunner):
        mock_load.return_value = {"rules": [], "chapters_analyzed": 0}
        result = runner.invoke(cli, ["profile"])
        assert result.exit_code == 0
        assert "No profile yet" in result.output

    @patch("editor.cli.load_profile")
    def test_displays_rules(self, mock_load: MagicMock, runner: CliRunner):
        mock_load.return_value = {
            "rules": [
                {
                    "category": "prose_tightening",
                    "rule": "Cut filter words",
                    "occurrences": 5,
                    "confidence": 0.88,
                    "examples": [{"before": "He felt pain.", "after": "Pain flared."}],
                }
            ],
            "chapters_analyzed": 3,
        }
        result = runner.invoke(cli, ["profile"])
        assert result.exit_code == 0
        assert "prose_tightening" in result.output
        assert "Cut filter words" in result.output
        assert "occurrences: 5" in result.output
        assert "Chapters analyzed: 3" in result.output


class TestResetCommand:
    @patch("editor.cli.reset_profile")
    def test_reset_confirmed(self, mock_reset: MagicMock, runner: CliRunner):
        result = runner.invoke(cli, ["reset", "--yes"])
        assert result.exit_code == 0
        assert "Profile reset" in result.output
        mock_reset.assert_called_once()

    @patch("editor.cli.reset_profile")
    def test_reset_aborted(self, mock_reset: MagicMock, runner: CliRunner):
        result = runner.invoke(cli, ["reset"], input="n\n")
        assert result.exit_code != 0 or "Aborted" in result.output
        mock_reset.assert_not_called()
