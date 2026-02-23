"""Click CLI — learn, profile, reset commands."""

from __future__ import annotations

import json
import sys

import click

from editor.analyzer import analyze_edits
from editor.differ import diff_files
from editor.profile import (
    PROFILE_PATH,
    load_profile,
    merge_patterns,
    reset_profile,
    save_profile,
)


@click.group()
def cli():
    """Style Editor — learn your editing patterns from markdown diffs."""


@cli.command()
@click.argument("original", type=click.Path(exists=True))
@click.argument("edited", type=click.Path(exists=True))
def learn(original: str, edited: str):
    """Run the full learning pipeline on ORIGINAL vs EDITED markdown files."""
    click.echo(f"Diffing: {original} → {edited}")

    edits = diff_files(original, edited)
    if not edits:
        click.echo("No differences found between the files.")
        return

    click.echo(f"Found {len(edits)} edit(s). Sending to Claude for analysis...")

    try:
        analysis = analyze_edits(edits)
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    pattern_count = sum(len(item.get("patterns", [])) for item in analysis)
    click.echo(f"Claude identified {pattern_count} pattern(s).")

    profile = load_profile()
    merge_patterns(profile, analysis)
    save_profile(profile)

    click.echo(
        f"Profile updated — {len(profile['rules'])} rule(s) across "
        f"{profile['chapters_analyzed']} chapter(s)."
    )
    click.echo(f"Saved to {PROFILE_PATH}")


@cli.command("profile")
def show_profile():
    """Print the current style profile."""
    profile = load_profile()
    if not profile.get("rules"):
        click.echo("No profile yet. Run 'learn' first.")
        return

    click.echo(f"Chapters analyzed: {profile['chapters_analyzed']}")
    click.echo(f"Total rules: {len(profile['rules'])}\n")

    # Sort by occurrences descending
    for rule in sorted(profile["rules"], key=lambda r: r.get("occurrences", 0), reverse=True):
        click.echo(f"  [{rule['category']}] {rule['rule']}")
        click.echo(f"    occurrences: {rule['occurrences']}  confidence: {rule['confidence']}")
        examples = rule.get("examples", [])
        if examples:
            ex = examples[0]
            click.echo(f'    example: "{ex.get("before", "")}" → "{ex.get("after", "")}"')
        click.echo()


@cli.command()
@click.confirmation_option(prompt="Delete the current style profile?")
def reset():
    """Delete the current style profile and start fresh."""
    reset_profile()
    click.echo("Profile reset.")


def main():
    cli()


if __name__ == "__main__":
    main()
