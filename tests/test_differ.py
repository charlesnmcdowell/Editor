"""Tests for the paragraph-level differ."""

from pathlib import Path

from editor.differ import Edit, diff_files, diff_paragraphs, split_paragraphs

FIXTURES = Path(__file__).parent / "fixtures"


class TestSplitParagraphs:
    def test_basic_split(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird."
        result = split_paragraphs(text)
        assert len(result) == 3
        assert result[0] == "First paragraph."
        assert result[2] == "Third."

    def test_strips_whitespace(self):
        text = "\n\n  Hello world  \n\n  Goodbye  \n\n"
        result = split_paragraphs(text)
        assert result == ["Hello world", "Goodbye"]

    def test_empty_string(self):
        assert split_paragraphs("") == []

    def test_single_paragraph(self):
        result = split_paragraphs("Just one block of text.")
        assert result == ["Just one block of text."]

    def test_preserves_internal_newlines(self):
        text = "Line one\nLine two\nLine three\n\nNext paragraph"
        result = split_paragraphs(text)
        assert len(result) == 2
        assert "Line one\nLine two\nLine three" == result[0]


class TestDiffParagraphs:
    def test_identical_returns_empty(self):
        text = "Same.\n\nAlso same."
        assert diff_paragraphs(text, text) == []

    def test_detects_replacement(self):
        orig = "Original paragraph one.\n\nUnchanged."
        edit = "Edited paragraph one.\n\nUnchanged."
        edits = diff_paragraphs(orig, edit)
        assert len(edits) == 1
        assert edits[0].original_text == "Original paragraph one."
        assert edits[0].edited_text == "Edited paragraph one."
        assert edits[0].paragraph_index == 0

    def test_detects_deletion(self):
        orig = "Keep this.\n\nDelete this.\n\nKeep this too."
        edit = "Keep this.\n\nKeep this too."
        edits = diff_paragraphs(orig, edit)
        assert len(edits) == 1
        assert edits[0].original_text == "Delete this."
        assert edits[0].edited_text == ""

    def test_detects_insertion(self):
        orig = "First.\n\nThird."
        edit = "First.\n\nInserted second.\n\nThird."
        edits = diff_paragraphs(orig, edit)
        assert len(edits) == 1
        assert edits[0].original_text == ""
        assert edits[0].edited_text == "Inserted second."

    def test_diff_summary_not_empty(self):
        orig = "Before.\n\nUnchanged."
        edit = "After.\n\nUnchanged."
        edits = diff_paragraphs(orig, edit)
        assert len(edits) == 1
        assert edits[0].diff_summary != ""

    def test_edit_type_initially_empty(self):
        orig = "A.\n\nB."
        edit = "A.\n\nC."
        edits = diff_paragraphs(orig, edit)
        assert edits[0].edit_type == ""


class TestDiffFiles:
    def test_fixture_files_produce_edits(self):
        edits = diff_files(FIXTURES / "original.md", FIXTURES / "edited.md")
        assert len(edits) > 0
        assert all(isinstance(e, Edit) for e in edits)

    def test_fixture_detects_known_changes(self):
        edits = diff_files(FIXTURES / "original.md", FIXTURES / "edited.md")
        # The first paragraph (after the title) was rewritten
        originals = [e.original_text for e in edits]
        assert any("He was tired from the long day" in o for o in originals)

    def test_fixture_detects_new_dialogue(self):
        edits = diff_files(FIXTURES / "original.md", FIXTURES / "edited.md")
        # "Nobody asked" dialogue line appears in edits (insert or replace)
        all_edited = [e.edited_text for e in edits]
        assert any("Nobody asked" in t for t in all_edited)
