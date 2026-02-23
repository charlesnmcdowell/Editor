"""Claude API caller for the editing workflow."""

from __future__ import annotations

import os

from anthropic import Anthropic
from dotenv import load_dotenv

from editor.prompts import AI_ONLY_SYSTEM, HUMAN_FEEDBACK_SYSTEM, PREFERENCE_EXTRACTION

load_dotenv()

MODEL = "claude-sonnet-4-20250514"
DELIMITER = "===FINAL==="


def _get_client() -> Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set. Add it to your .env file.")
    return Anthropic(api_key=api_key)


def _call_claude(system: str, user_content: str, max_tokens: int = 16384) -> str:
    """Make a single Claude API call and return the text response."""
    client = _get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text


def edit_with_feedback(
    original: str,
    feedback: str,
    preferences: str,
) -> tuple[str, str]:
    """Human Feedback Mode: edit a chapter using human feedback + preferences.

    Returns (reasoning, final_chapter).
    """
    user_content = (
        f"ORIGINAL:\n{original}\n\n"
        f"FEEDBACK:\n{feedback}\n\n"
        f"PREFERENCES:\n{preferences if preferences else '(No preferences established yet — this is the first session.)'}"
    )
    raw = _call_claude(HUMAN_FEEDBACK_SYSTEM, user_content)
    return _split_output(raw)


def edit_ai_only(
    original: str,
    preferences: str,
) -> tuple[str, str]:
    """AI-Only Mode: edit a chapter using only established preferences.

    Returns (reasoning, final_chapter).
    """
    user_content = (
        f"ORIGINAL:\n{original}\n\n"
        f"PREFERENCES:\n{preferences if preferences else '(No preferences established yet. Apply general fiction-editing best practices conservatively.)'}"
    )
    raw = _call_claude(AI_ONLY_SYSTEM, user_content)
    return _split_output(raw)


def update_preferences(
    original: str,
    feedback: str,
    final: str,
    current_preferences: str,
) -> str:
    """Extract new style preferences from human feedback.

    Returns the updated authorpreferences.md content (plain English).
    """
    prompt = PREFERENCE_EXTRACTION.format(
        original=original,
        feedback=feedback,
        final=final,
        current_preferences=current_preferences if current_preferences else "(No existing preferences — this is the first session.)",
    )
    return _call_claude(
        "You are a style-preference analyst for a fiction author.",
        prompt,
        max_tokens=4096,
    )


def _split_output(raw: str) -> tuple[str, str]:
    """Split Claude's response on ===FINAL=== into (reasoning, chapter)."""
    if DELIMITER not in raw:
        # Fallback: treat entire response as the final chapter, no reasoning
        return ("(No reasoning section found in response.)", raw.strip())

    parts = raw.split(DELIMITER, 1)
    reasoning = parts[0].strip()
    final = parts[1].strip()
    return (reasoning, final)
