"""Tests for analyzer module — unit tests with mocked API calls."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from editor.analyzer import _build_user_prompt, analyze_edits
from editor.differ import Edit


def _make_edit(**overrides) -> Edit:
    defaults = dict(
        original_text="He was tired.",
        edited_text="Tired didn't cover it.",
        paragraph_index=1,
        diff_summary="- He was tired.\n+ Tired didn't cover it.",
        edit_type="",
    )
    defaults.update(overrides)
    return Edit(**defaults)


class TestBuildUserPrompt:
    def test_returns_valid_json(self):
        edits = [_make_edit()]
        raw = _build_user_prompt(edits)
        parsed = json.loads(raw)
        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_truncates_long_text(self):
        edits = [_make_edit(original_text="x" * 1000)]
        raw = _build_user_prompt(edits)
        parsed = json.loads(raw)
        assert len(parsed[0]["original_text"]) == 500

    def test_empty_list(self):
        raw = _build_user_prompt([])
        assert json.loads(raw) == []


class TestAnalyzeEdits:
    def test_empty_edits_returns_empty(self):
        assert analyze_edits([]) == []

    def test_raises_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                analyze_edits([_make_edit()])

    @patch("editor.analyzer.Anthropic")
    def test_parses_valid_response(self, mock_anthropic_cls):
        expected = [
            {
                "paragraph_index": 1,
                "patterns": [
                    {
                        "category": "prose_tightening",
                        "rule": "Replace filter words with direct experience",
                        "confidence": 0.9,
                        "example_before": "He was tired.",
                        "example_after": "Tired didn't cover it.",
                    }
                ],
            }
        ]
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(expected))]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = analyze_edits([_make_edit()])

        assert result == expected
        mock_client.messages.create.assert_called_once()

    @patch("editor.analyzer.Anthropic")
    def test_strips_markdown_fences(self, mock_anthropic_cls):
        expected = [{"paragraph_index": 1, "patterns": []}]
        fenced = f"```json\n{json.dumps(expected)}\n```"
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=fenced)]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = analyze_edits([_make_edit()])

        assert result == expected

    @patch("editor.analyzer.Anthropic")
    def test_raises_on_invalid_json(self, mock_anthropic_cls):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="This is not JSON")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with pytest.raises(RuntimeError, match="invalid JSON"):
                analyze_edits([_make_edit()])

    @patch("editor.analyzer.Anthropic")
    def test_raises_on_non_list_response(self, mock_anthropic_cls):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text='{"not": "a list"}')]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with pytest.raises(RuntimeError, match="JSON array"):
                analyze_edits([_make_edit()])
