"""Send edit diffs to Claude API for style-pattern categorization."""

from __future__ import annotations

import json
import os
from dataclasses import asdict

from anthropic import Anthropic
from dotenv import load_dotenv

from editor.differ import Edit

load_dotenv()

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """\
You are an expert literary editor analyst. You will receive a list of edits \
made to a fiction manuscript. Each edit contains the original text, the edited \
text, paragraph index, and a diff summary.

Your job is to categorize every edit into one or more editing-style patterns. \
Return ONLY valid JSON — no markdown fences, no commentary.

The JSON must be a list of objects, one per edit, each with these fields:
- paragraph_index (int): the paragraph index of the edit
- patterns (list of objects): each pattern has:
  - category (str): one of prose_tightening, dialogue_adjustment, \
pacing_changes, tone_shifts, show_vs_tell, internal_monologue, \
combat_writing, world_building, sensory_detail, metaphor_refinement, \
voice_consistency, repetition_removal, sentence_structure, other
  - rule (str): a short, reusable description of the editing rule applied \
(e.g. "Replace filter words with direct sensory experience")
  - confidence (float): 0.0 to 1.0
  - example_before (str): brief excerpt from original
  - example_after (str): brief excerpt from edited version

Respond with ONLY the JSON array. No preamble. No closing remarks.\
"""


def _build_user_prompt(edits: list[Edit]) -> str:
    """Serialize edits into a prompt for Claude."""
    items = []
    for e in edits:
        items.append(
            {
                "paragraph_index": e.paragraph_index,
                "original_text": e.original_text[:500],
                "edited_text": e.edited_text[:500],
                "diff_summary": e.diff_summary[:300],
            }
        )
    return json.dumps(items, indent=2)


def analyze_edits(edits: list[Edit]) -> list[dict]:
    """Send edits to Claude and return categorized patterns.

    Returns a list of dicts, one per edit, each containing
    ``paragraph_index`` and ``patterns``.
    """
    if not edits:
        return []

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to your .env file."
        )

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _build_user_prompt(edits)},
        ],
    )

    raw = response.content[0].text.strip()

    # Safety: strip markdown fences if Claude adds them despite instructions
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Claude returned invalid JSON. Raw response:\n{raw}"
        ) from exc

    if not isinstance(result, list):
        raise RuntimeError(
            f"Expected a JSON array from Claude, got {type(result).__name__}."
        )

    return result
