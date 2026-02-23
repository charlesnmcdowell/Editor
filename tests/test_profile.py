"""Tests for the profile merge / persistence logic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from editor.profile import (
    _rules_match,
    load_profile,
    merge_patterns,
    reset_profile,
    save_profile,
)


@pytest.fixture
def tmp_profile(tmp_path: Path) -> Path:
    return tmp_path / "style_profile.json"


class TestRulesMatch:
    def test_identical_rules_match(self):
        assert _rules_match("Remove filter words", "Remove filter words")

    def test_similar_rules_match(self):
        assert _rules_match(
            "Replace filter words with direct sensory experience",
            "Remove filter words and use direct sensory detail",
        )

    def test_different_rules_dont_match(self):
        assert not _rules_match(
            "Tighten dialogue tags",
            "Add sensory detail to environment descriptions",
        )

    def test_empty_rules_dont_match(self):
        assert not _rules_match("", "")
        assert not _rules_match("some rule", "")


class TestLoadSaveProfile:
    def test_load_nonexistent_returns_blank(self, tmp_profile: Path):
        profile = load_profile(tmp_profile)
        assert profile == {"rules": [], "chapters_analyzed": 0}

    def test_save_and_load_roundtrip(self, tmp_profile: Path):
        data = {
            "rules": [
                {
                    "category": "prose_tightening",
                    "rule": "Cut filter words",
                    "occurrences": 3,
                    "confidence": 0.85,
                    "examples": [],
                }
            ],
            "chapters_analyzed": 2,
        }
        save_profile(data, tmp_profile)
        loaded = load_profile(tmp_profile)
        assert loaded == data

    def test_save_creates_parent_dirs(self, tmp_path: Path):
        deep = tmp_path / "a" / "b" / "profile.json"
        save_profile({"rules": [], "chapters_analyzed": 0}, deep)
        assert deep.exists()


class TestMergePatterns:
    def _make_analysis(self, category="prose_tightening", rule="Cut filter words"):
        return [
            {
                "paragraph_index": 0,
                "patterns": [
                    {
                        "category": category,
                        "rule": rule,
                        "confidence": 0.9,
                        "example_before": "He felt tired.",
                        "example_after": "Tired didn't cover it.",
                    }
                ],
            }
        ]

    def test_adds_new_rule(self):
        profile = {"rules": [], "chapters_analyzed": 0}
        merge_patterns(profile, self._make_analysis())
        assert len(profile["rules"]) == 1
        assert profile["rules"][0]["occurrences"] == 1
        assert profile["chapters_analyzed"] == 1

    def test_increments_matching_rule(self):
        profile = {
            "rules": [
                {
                    "category": "prose_tightening",
                    "rule": "Cut filter words",
                    "occurrences": 2,
                    "confidence": 0.8,
                    "examples": [],
                }
            ],
            "chapters_analyzed": 1,
        }
        merge_patterns(
            profile,
            self._make_analysis(rule="Remove filter words from prose"),
        )
        assert profile["rules"][0]["occurrences"] == 3
        assert len(profile["rules"]) == 1  # no duplicate added
        assert profile["chapters_analyzed"] == 2

    def test_different_category_creates_new(self):
        profile = {
            "rules": [
                {
                    "category": "prose_tightening",
                    "rule": "Cut filter words",
                    "occurrences": 1,
                    "confidence": 0.8,
                    "examples": [],
                }
            ],
            "chapters_analyzed": 0,
        }
        merge_patterns(
            profile,
            self._make_analysis(category="dialogue_adjustment", rule="Cut filter words"),
        )
        assert len(profile["rules"]) == 2

    def test_empty_analysis_still_increments_chapter(self):
        profile = {"rules": [], "chapters_analyzed": 5}
        merge_patterns(profile, [])
        assert profile["chapters_analyzed"] == 6


class TestResetProfile:
    def test_reset_deletes_file(self, tmp_profile: Path):
        save_profile({"rules": [], "chapters_analyzed": 0}, tmp_profile)
        assert tmp_profile.exists()
        reset_profile(tmp_profile)
        assert not tmp_profile.exists()

    def test_reset_nonexistent_no_error(self, tmp_profile: Path):
        reset_profile(tmp_profile)  # should not raise
