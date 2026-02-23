"""Merge analyzed patterns into a persistent style_profile.json."""

from __future__ import annotations

import json
from pathlib import Path

PROFILE_PATH = Path(__file__).resolve().parent.parent / "output" / "style_profile.json"


def _keyword_set(rule: str) -> set[str]:
    """Extract lowercase keyword tokens from a rule string for overlap matching."""
    stop = {
        "a", "an", "the", "and", "or", "of", "to", "in", "is", "it",
        "for", "with", "on", "at", "by", "from", "that", "this", "as",
    }
    words = set(rule.lower().split())
    return words - stop


def _rules_match(existing_rule: str, new_rule: str, threshold: float = 0.4) -> bool:
    """Return True if two rule strings share enough keyword overlap."""
    a = _keyword_set(existing_rule)
    b = _keyword_set(new_rule)
    if not a or not b:
        return False
    overlap = len(a & b)
    smaller = min(len(a), len(b))
    return (overlap / smaller) >= threshold


def load_profile(path: Path | None = None) -> dict:
    """Load the current style profile from disk, or return a blank one."""
    p = path or PROFILE_PATH
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"rules": [], "chapters_analyzed": 0}


def save_profile(profile: dict, path: Path | None = None) -> None:
    """Write the profile to disk."""
    p = path or PROFILE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")


def merge_patterns(profile: dict, analysis_results: list[dict]) -> dict:
    """Merge new analysis results into an existing profile.

    For each pattern in the analysis:
    - If a rule with sufficient keyword overlap exists, increment its
      occurrence count and append the new example.
    - Otherwise, add it as a new rule.

    Returns the updated profile (also mutates in place).
    """
    existing_rules: list[dict] = profile.setdefault("rules", [])
    profile.setdefault("chapters_analyzed", 0)
    profile["chapters_analyzed"] += 1

    for item in analysis_results:
        for pattern in item.get("patterns", []):
            category = pattern.get("category", "other")
            rule = pattern.get("rule", "")
            confidence = pattern.get("confidence", 0.5)
            example = {
                "before": pattern.get("example_before", ""),
                "after": pattern.get("example_after", ""),
            }

            # Try to find a matching existing rule
            matched = False
            for existing in existing_rules:
                if (
                    existing.get("category") == category
                    and _rules_match(existing.get("rule", ""), rule)
                ):
                    existing["occurrences"] = existing.get("occurrences", 1) + 1
                    existing.setdefault("examples", []).append(example)
                    # Running average of confidence
                    n = existing["occurrences"]
                    old_conf = existing.get("confidence", confidence)
                    existing["confidence"] = round(
                        ((old_conf * (n - 1)) + confidence) / n, 3
                    )
                    matched = True
                    break

            if not matched:
                existing_rules.append(
                    {
                        "category": category,
                        "rule": rule,
                        "occurrences": 1,
                        "confidence": confidence,
                        "examples": [example],
                    }
                )

    return profile


def reset_profile(path: Path | None = None) -> None:
    """Delete the style profile from disk."""
    p = path or PROFILE_PATH
    if p.exists():
        p.unlink()
