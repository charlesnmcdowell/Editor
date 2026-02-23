# Changelog

## [0.2.0] - 2026-02-23

### Changed — Stage 2: File-Based Editing Workflow

Replaced the Stage 1 diff/analyze/profile pipeline with a simpler, file-based editing workflow. One command (`python -m editor.cli edit`) handles everything.

**New workflow:**

The system reads `original.md` (raw chapter) and `edited.md` (optional human feedback). If feedback exists, it runs in **Human Feedback Mode** — Claude applies the feedback plus any established author preferences to produce the edited chapter. If no feedback, it runs in **AI-Only Mode** — Claude applies only learned preferences conservatively. After editing, files are archived to `history/` with timestamps and working files are wiped for the next chapter.

**New/rebuilt modules:**

- **`editor/prompts.py`** (new) — All Claude system prompts in one place: human feedback editing, AI-only editing, and preference extraction.
- **`editor/analyzer.py`** (rebuilt) — Claude API caller with three functions: `edit_with_feedback()`, `edit_ai_only()`, `update_preferences()`. Uses `===FINAL===` delimiter to split reasoning from clean chapter output.
- **`editor/profile.py`** (rebuilt) — Simple file I/O for all working files (`original.md`, `edited.md`, `aiedited.md`, `final.md`, `authorpreferences.md`). No more JSON profile; preferences are plain English in a markdown file.
- **`editor/archive.py`** (new) — Timestamped archiving. Creates `history/{YYYY-MM-DD_HHMMSS}_{human|ai}/` folders, copies relevant files, then wipes working files. Also provides `list_history()` for the CLI.
- **`editor/cli.py`** (rebuilt) — Four Click commands:
  - `edit` — the main workflow (detects mode, calls Claude, writes outputs, updates prefs, archives)
  - `preferences` — prints current `authorpreferences.md`
  - `history` — lists archived sessions
  - `reset --yes` — deletes `authorpreferences.md`

**Removed:**

- **`editor/differ.py`** — Paragraph-level diffing no longer needed; Claude reads files directly.
- `output/style_profile.json` workflow — replaced by plain-English `authorpreferences.md`.

**Working files (repo root):**

- `original.md` — raw chapter text (user fills this)
- `edited.md` — human feedback inline comments (optional; may be empty)
- `aiedited.md` — AI reasoning log (auto-generated)
- `final.md` — clean edited chapter (auto-generated)
- `authorpreferences.md` — persistent style memory, plain English, grows over time

**Test suite (42 tests, all passing):**

- `tests/test_analyzer.py` (8 tests) — output splitting, both edit modes, preference extraction, all mocked
- `tests/test_archive.py` (10 tests) — human/AI archiving, file copying, wiping, history listing
- `tests/test_cli.py` (9 tests) — all four CLI commands with mocked dependencies
- `tests/test_profile.py` (15 tests) — file read/write, load/save helpers, wipe, reset

---

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
