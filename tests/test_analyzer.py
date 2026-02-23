"""Tests for the Stage 2 analyzer — Claude API calls with mocked responses."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from editor.analyzer import (
    _split_output,
    edit_ai_only,
    edit_with_feedback,
    update_preferences,
)


SAMPLE_RESPONSE = """\
## Reasoning
Changed "He was tired" to "Tired didn't cover it" — applying feedback [too wordy].

===FINAL===

# Chapter 1

Tired didn't cover it.\
"""


class TestSplitOutput:
    def test_splits_on_delimiter(self):
        reasoning, final = _split_output(SAMPLE_RESPONSE)
        assert "Reasoning" in reasoning
        assert "Tired didn't cover it." in final
        assert "===FINAL===" not in reasoning
        assert "===FINAL===" not in final

    def test_no_delimiter_returns_full_as_final(self):
        raw = "Just a chapter with no delimiter."
        reasoning, final = _split_output(raw)
        assert "No reasoning" in reasoning
        assert final == "Just a chapter with no delimiter."

    def test_strips_whitespace(self):
        raw = "  reasoning  \n\n===FINAL===\n\n  chapter  \n"
        reasoning, final = _split_output(raw)
        assert reasoning == "reasoning"
        assert final == "chapter"


class TestEditWithFeedback:
    @patch("editor.analyzer._call_claude")
    def test_returns_reasoning_and_final(self, mock_call):
        mock_call.return_value = SAMPLE_RESPONSE

        reasoning, final = edit_with_feedback(
            original="He was tired.",
            feedback="[too wordy]",
            preferences="Keep it tight.",
        )
        assert "Reasoning" in reasoning
        assert "Tired didn't cover it." in final
        mock_call.assert_called_once()

    @patch("editor.analyzer._call_claude")
    def test_empty_preferences_handled(self, mock_call):
        mock_call.return_value = "reason\n===FINAL===\nchapter"

        reasoning, final = edit_with_feedback("text", "feedback", "")
        assert final == "chapter"
        # Verify the prompt includes the "no preferences" note
        call_args = mock_call.call_args
        assert "first session" in call_args[0][1].lower() or "no preferences" in call_args[0][1].lower()


class TestEditAiOnly:
    @patch("editor.analyzer._call_claude")
    def test_returns_reasoning_and_final(self, mock_call):
        mock_call.return_value = "Applied rule X.\n===FINAL===\nEdited chapter."

        reasoning, final = edit_ai_only("Original text.", "Be concise.")
        assert reasoning == "Applied rule X."
        assert final == "Edited chapter."

    @patch("editor.analyzer._call_claude")
    def test_empty_preferences_handled(self, mock_call):
        mock_call.return_value = "reason\n===FINAL===\nchapter"

        edit_ai_only("text", "")
        call_args = mock_call.call_args
        assert "best practices" in call_args[0][1].lower() or "no preferences" in call_args[0][1].lower()


class TestUpdatePreferences:
    @patch("editor.analyzer._call_claude")
    def test_returns_updated_preferences(self, mock_call):
        mock_call.return_value = "# Author Preferences\n\n## Prose\n- Keep descriptions concise."

        result = update_preferences(
            original="Long wordy text.",
            feedback="[too wordy]",
            final="Concise text.",
            current_preferences="",
        )
        assert "Author Preferences" in result
        mock_call.assert_called_once()
