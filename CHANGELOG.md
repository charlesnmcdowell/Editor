# Changelog

## [0.1.0] - 2026-02-23

### Added — Stage 1: Learning Pipeline

**Core modules:**

- **`editor/differ.py`** — Paragraph-level diffing engine. Splits markdown files on double-newline boundaries, aligns paragraphs with `difflib.SequenceMatcher`, and produces `Edit` dataclass objects containing original text, edited text, paragraph index, and a unified diff summary. Handles replacements, insertions, and deletions.

- **`editor/analyzer.py`** — Claude API integration. Sends edit lists to `claude-sonnet-4-20250514` with a structured system prompt that forces JSON-only responses. Categorizes each edit into patterns such as `prose_tightening`, `dialogue_adjustment`, `pacing_changes`, `tone_shifts`, `show_vs_tell`, `internal_monologue`, `combat_writing`, `world_building`, `sensory_detail`, `metaphor_refinement`, `voice_consistency`, `repetition_removal`, `sentence_structure`, and `other`. Includes safety stripping for markdown fences.

- **`editor/profile.py`** — Profile accumulation engine. Merges new analysis results into `output/style_profile.json`. Uses keyword-overlap matching (40% threshold on the smaller set) to detect when a new rule duplicates an existing one — if matched, increments the occurrence count, appends the new example, and updates the running confidence average. New rules get their own entry. Tracks total chapters analyzed.

- **`editor/cli.py`** — Click CLI with three commands:
  - `learn <original.md> <edited.md>` — runs the full pipeline: diff → analyze → merge → save
  - `profile` — prints the current style profile sorted by occurrence count
  - `reset --yes` — deletes the profile and starts fresh

**Test suite (43 tests, all passing):**

- `tests/test_differ.py` (14 tests) — paragraph splitting, replacement/insertion/deletion detection, fixture file integration
- `tests/test_analyzer.py` (9 tests) — prompt building, API mocking, JSON parsing, error handling
- `tests/test_profile.py` (13 tests) — rule matching, load/save roundtrip, merge logic, reset
- `tests/test_cli.py` (7 tests) — all three CLI commands with mocked dependencies

**Infrastructure:**

- `requirements.txt` — anthropic, python-dotenv, click, pytest
- `.env.example` — template for API key
- `.gitignore` — excludes `__pycache__`, `.env`, `style_profile.json`, `.venv`
- `.cursor/rules/editor-tool.mdc` — project conventions for AI-assisted development
- `tests/fixtures/original.md` + `edited.md` — sample chapter pair for testing
- `output/.gitkeep` — placeholder for profile output directory
