"""Click CLI — edit, preferences, history, reset commands."""

from __future__ import annotations

import sys

import click

from editor.analyzer import edit_ai_only, edit_with_feedback, update_preferences
from editor.archive import archive_ai_only, archive_human_feedback, list_history
from editor.profile import (
    load_feedback,
    load_original,
    load_preferences,
    reset_preferences,
    save_final,
    save_preferences,
    save_reasoning,
)


@click.group()
def cli():
    """Style Editor — file-based editing workflow powered by Claude."""


@cli.command()
def edit():
    """Run the full editing workflow.

    Reads original.md and edited.md, detects mode (human feedback vs AI-only),
    calls Claude, writes aiedited.md and final.md, updates preferences if
    applicable, and archives everything.
    """
    # 1. Read original.md
    original = load_original()
    if not original:
        click.echo("Error: original.md is empty. Add chapter content first.", err=True)
        sys.exit(1)

    click.echo(f"Read original.md ({len(original)} chars)")

    # 2. Read edited.md to detect mode
    feedback = load_feedback()
    preferences = load_preferences()

    if preferences:
        click.echo(f"Loaded authorpreferences.md ({len(preferences)} chars)")
    else:
        click.echo("No authorpreferences.md yet (first run or reset)")

    # 3. Dispatch based on mode
    if feedback:
        click.echo("\n--- HUMAN FEEDBACK MODE ---")
        click.echo(f"Feedback found in edited.md ({len(feedback)} chars)")
        click.echo("Sending to Claude for editing...")

        try:
            reasoning, final = edit_with_feedback(original, feedback, preferences)
        except RuntimeError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

        save_reasoning(reasoning)
        save_final(final)
        click.echo(f"Wrote aiedited.md ({len(reasoning)} chars)")
        click.echo(f"Wrote final.md ({len(final)} chars)")

        # Update preferences from human feedback
        click.echo("Extracting style preferences from feedback...")
        try:
            new_prefs = update_preferences(original, feedback, final, preferences)
        except RuntimeError as exc:
            click.echo(f"Warning: preference update failed: {exc}", err=True)
            new_prefs = None

        if new_prefs:
            save_preferences(new_prefs)
            click.echo(f"Updated authorpreferences.md ({len(new_prefs)} chars)")

        # Archive and wipe
        archive_dir = archive_human_feedback()
        click.echo(f"\nArchived to {archive_dir}")

    else:
        click.echo("\n--- AI-ONLY MODE ---")
        click.echo("No feedback in edited.md. Editing with preferences only.")
        click.echo("Sending to Claude for editing...")

        try:
            reasoning, final = edit_ai_only(original, preferences)
        except RuntimeError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

        save_reasoning(reasoning)
        save_final(final)
        click.echo(f"Wrote aiedited.md ({len(reasoning)} chars)")
        click.echo(f"Wrote final.md ({len(final)} chars)")

        # No preference update in AI-only mode
        click.echo("(Skipping preference update — no human feedback)")

        # Archive and wipe
        archive_dir = archive_ai_only()
        click.echo(f"\nArchived to {archive_dir}")

    click.echo("Done.")


@cli.command("preferences")
def show_preferences():
    """Print the current authorpreferences.md to the terminal."""
    prefs = load_preferences()
    if not prefs:
        click.echo("No preferences yet. Run an edit with human feedback first.")
        return
    click.echo(prefs)


@cli.command("history")
def show_history():
    """List all archived edit sessions."""
    sessions = list_history()
    if not sessions:
        click.echo("No archived sessions yet.")
        return

    click.echo(f"{len(sessions)} archived session(s):\n")
    for s in sessions:
        mode_label = "Human Feedback" if s["mode"] == "human" else "AI-Only"
        click.echo(f"  {s['name']}  [{mode_label}]")
        for f in s["files"]:
            click.echo(f"    - {f}")
        click.echo()


@cli.command()
@click.confirmation_option(prompt="Delete authorpreferences.md and start fresh?")
def reset():
    """Delete authorpreferences.md and start fresh."""
    if reset_preferences():
        click.echo("authorpreferences.md deleted.")
    else:
        click.echo("No authorpreferences.md found — nothing to reset.")


def main():
    cli()


if __name__ == "__main__":
    main()
