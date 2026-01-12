"""CLI commands for the text content pipeline."""

import asyncio
import json
import sys
from pathlib import Path

import click

from src.ai_generator import generator
from src.weekly_calendar.resolver import resolve_calendar
from src.config.defaults import (
    COLORFUL_PRESETS,
    DEFAULT_AI_MODEL,
)
from src.errors.exceptions import (
    ModelUnavailableError,
    PipelineError,
)
from src.payload import schema, validation
from src.pipeline import orchestrator
from src.renderer import html_renderer


@click.group()
def cli() -> None:
    """Text content pipeline - Convert monthly themes into daily images."""
    pass


@cli.command()
@click.argument("year", type=int)
@click.argument("month", type=int)
@click.option("--theme", help="Monthly theme (optional, can edit later)")
@click.option("--output", "-o", help="Output path for payload file")
def init_month(year: int, month: int, theme: str | None, output: str | None) -> None:
    """Initialize a new month payload file.

    Example:
        init-month 2026 2 --theme "Evolving in Christ"
    """
    if output is None:
        output = f"{year:04d}-{month:02d}_payload.json"

    payload_path = Path(output)

    if payload_path.exists():
        click.echo(f"Error: Payload file already exists: {output}", err=True)
        sys.exit(1)

    # Create payload scaffold
    if theme is None:
        theme = "Your monthly theme here"

    payload_data = {
        "year": year,
        "month": month,
        "monthly_theme": theme,
        "weekly_subthemes": None,
        "week_rule": "monday_determines_month",
        "video_week": "last_week",
        "style_preset": "default",
        "notes": None,
    }

    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload_data, f, indent=2, ensure_ascii=False)

    click.echo(f"✓ Created payload file: {output}")
    click.echo(f"  Year: {year}")
    click.echo(f"  Month: {month:02d}")
    click.echo(f"  Theme: {theme}")
    click.echo(f"\nEdit this file to add your weekly subthemes and adjust settings.")


@cli.command()
@click.option("--payload", type=click.Path(exists=True), help="Path to payload JSON file")
@click.option("--theme", help="Monthly theme (if not providing payload file)")
@click.option("--year", type=int, help="Year (required with --theme)")
@click.option("--month", type=int, help="Month (required with --theme)")
@click.option("--subthemes", help="Comma-separated weekly subthemes (optional with --theme)")
def validate(
    payload: str | None,
    theme: str | None,
    year: int | None,
    month: int | None,
    subthemes: str | None,
) -> None:
    """Validate a month payload without running pipeline.

    Example:
        validate --payload 2026-02_payload.json
        validate --theme "Evolving in Christ" --year 2026 --month 2
    """
    try:
        # Validate: either payload or theme/year/month
        if payload is None:
            if not theme or year is None or month is None:
                click.echo("✗ With --theme, must also provide --year and --month", err=True)
                sys.exit(1)

            # Create temporary payload
            weekly_subthemes_list = None
            if subthemes:
                weekly_subthemes_list = [s.strip() for s in subthemes.split(",")]

            payload_data = {
                "year": year,
                "month": month,
                "monthly_theme": theme,
                "weekly_subthemes": weekly_subthemes_list,
                "week_rule": "monday_determines_month",
                "video_week": "last_week",
                "style_preset": "default",
                "notes": None,
            }

            # Parse payload
            payload_obj = schema.MonthlyPayload(**payload_data)
        else:
            with open(payload, "r", encoding="utf-8") as f:
                payload_data = json.load(f)

            payload_obj = schema.MonthlyPayload(**payload_data)

        validation.validate_payload(payload_obj)

        click.echo("✓ Payload is valid:")
        click.echo(f"  Year: {payload_obj.year}")
        click.echo(f"  Month: {payload_obj.month:02d}")
        click.echo(f"  Theme: {payload_obj.monthly_theme}")
        if payload_obj.weekly_subthemes:
            click.echo(f"  Weekly subthemes: {len(payload_obj.weekly_subthemes)} provided")
        else:
            click.echo("  Weekly subthemes: will be derived by AI")
        click.echo(f"  Style preset: {payload_obj.style_preset}")
        click.echo(f"  Video week: {payload_obj.video_week}")

    except Exception as e:
        click.echo(f"✗ Validation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("payload_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output path for calendar JSON")
def resolve_calendar_cmd(payload_path: str, output: str | None) -> None:
    """Run Stage 1 only: resolve calendar.

    Example:
        resolve-calendar 2026-02_payload.json
    """
    try:
        with open(payload_path, "r", encoding="utf-8") as f:
            payload_data = json.load(f)

        payload = schema.MonthlyPayload(**payload_data)
        calendar = resolve_calendar(payload)

        calendar_data = {
            "year": calendar.year,
            "month": calendar.month,
            "monthly_theme": calendar.monthly_theme,
            "weekly_subthemes": calendar.weekly_subthemes,
            "weeks": [
                {
                    "week_number": w.week_number,
                    "monday_date": w.monday_date,
                    "sunday_date": w.sunday_date,
                    "subtheme": w.subtheme,
                    "is_video_week": w.is_video_week,
                }
                for w in calendar.weeks
            ],
        }

        if output is None:
            output = f"{calendar.year}-{calendar.month:02d}_calendar.json"

        with open(output, "w", encoding="utf-8") as f:
            json.dump(calendar_data, f, indent=2, ensure_ascii=False)

        click.echo(f"✓ Resolved calendar saved to: {output}")
        click.echo(f"  Weeks: {len(calendar.weeks)}")
        click.echo(f"  Video week: {calendar.weeks[-1].week_number} (last)")

    except Exception as e:
        click.echo(f"✗ Calendar resolution failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--payload", type=click.Path(exists=True), help="Path to payload JSON file")
@click.option("--theme", help="Monthly theme (if not providing payload file)")
@click.option("--year", type=int, help="Year (required with --theme)")
@click.option("--month", type=int, help="Month (required with --theme)")
@click.option("--subthemes", help="Comma-separated weekly subthemes (optional with --theme)")
@click.option("--skip-rendering", is_flag=True, help="Skip image rendering")
@click.option("--skip-text", is_flag=True, help="Skip AI text generation")
@click.option("--model", help="Override AI model (e.g., gpt-oss:20b)")
@click.option("--background-color", help="Override background color (e.g., #4A90E2)")
def run_all(
    payload: str | None,
    theme: str | None,
    year: int | None,
    month: int | None,
    subthemes: str | None,
    skip_rendering: bool,
    skip_text: bool,
    model: str | None,
    background_color: str | None,
) -> None:
    """Run full pipeline end-to-end.

    Example:
        run-all --payload 2026-02_payload.json
        run-all --theme "Evolving in Christ" --year 2026 --month 2
        run-all --theme "Evolving in Christ" --year 2026 --month 2 --skip-rendering
    """
    # Validate: either payload or theme/year/month
    if payload is None:
        if not theme or year is None or month is None:
            click.echo("✗ With --theme, must also provide --year and --month", err=True)
            sys.exit(1)

        # Create temporary payload
        weekly_subthemes_list = None
        if subthemes:
            weekly_subthemes_list = [s.strip() for s in subthemes.split(",")]

        payload_data = {
            "year": year,
            "month": month,
            "monthly_theme": theme,
            "weekly_subthemes": weekly_subthemes_list,
            "week_rule": "monday_determines_month",
            "video_week": "last_week",
            "style_preset": "default",
            "notes": None,
        }

        # Save temp payload
        payload_path = Path("outputs/plans/temp_payload.json")
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        with open(payload_path, "w", encoding="utf-8") as f:
            json.dump(payload_data, f, indent=2, ensure_ascii=False)

        click.echo(f"✓ Created temporary payload: {payload_path}")
    else:
        payload_path = Path(payload)

    try:
        # Check model availability if generating text
        if not skip_text:
            click.echo("Checking AI model availability...")
            available = asyncio.run(generator.check_model_available())
            if not available:
                click.echo(
                    f"✗ Model '{DEFAULT_AI_MODEL}' not found in Ollama.",
                    err=True,
                )
                click.echo(f"  Please run: ollama pull {DEFAULT_AI_MODEL}")
                sys.exit(1)

        # Run pipeline
        results = asyncio.run(
            orchestrator.validate_and_run(
                str(payload_path),
                model=model,
                background_color=background_color,
                skip_rendering=skip_rendering,
                skip_text_generation=skip_text,
            )
        )

        # Summary
        click.echo(f"\n✓ Pipeline completed successfully!")
        click.echo(f"  Plan saved: {results['plan_path']}")
        if not skip_text:
            click.echo(f"  Generated texts: {len(results['generated_texts'])}")
        if not skip_rendering:
            click.echo(f"  Rendered images: {len(results['rendered_images'])}")

    except ModelUnavailableError as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)
    except PipelineError as e:
        click.echo(f"✗ Pipeline failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_presets() -> None:
    """List available colorful style presets."""
    click.echo("Available style presets (colorful backgrounds only):")
    for name, preset in COLORFUL_PRESETS.items():
        click.echo(f"  {name}:")
        click.echo(f"    Background: {preset['background']}")
        click.echo(f"    Text: {preset['text_color']}")


@cli.command()
@click.argument("preset_name", type=str)
def show_preset(preset_name: str) -> None:
    """Show details of a specific style preset."""
    if preset_name not in COLORFUL_PRESETS:
        click.echo(f"✗ Unknown preset: {preset_name}", err=True)
        click.echo(f"  Available: {list(COLORFUL_PRESETS.keys())}")
        sys.exit(1)

    preset = COLORFUL_PRESETS[preset_name]
    click.echo(f"Preset: {preset_name}")
    click.echo(f"  Background: {preset['background']}")
    click.echo(f"  Text color: {preset['text_color']}")
    click.echo(f"  Font size: {preset['font_size']}px")
    click.echo(f"  Padding: {preset['padding']}px")


@cli.command()
@click.argument("payload_path", type=click.Path(exists=True))
def inspect_plan(payload_path: str) -> None:
    """Inspect the generated slot plan for a month."""
    # Find the plan file
    with open(payload_path, "r", encoding="utf-8") as f:
        payload_data = json.load(f)

    year = payload_data["year"]
    month = payload_data["month"]
    plan_path = Path(f"outputs/plans/{year}-{month:02d}_plan.json")

    if not plan_path.exists():
        click.echo(f"✗ No plan found for {year}-{month:02d}", err=True)
        click.echo(f"  Run 'run-all' first to generate a plan.")
        sys.exit(1)

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    click.echo(f"Plan for {plan_data['monthly_theme']}")
    click.echo(f"Source: {plan_data['weekly_subthemes_source']}")
    click.echo(f"\nWeekly subthemes:")
    for i, subtheme in enumerate(plan_data.get("weekly_subthemes", [])):
        click.echo(f"  Week {i+1}: {subtheme}")

    click.echo(f"\nSlot schedule:")
    for slot in plan_data["schedule_summary"]:
        status = "AUTO" if slot["is_automated"] else "HUMAN"
        click.echo(f"  {slot['date']} ({slot['weekday']}): {slot['slot_type']} [{status}]")


@cli.command()
@click.option("--theme", help="Monthly theme (default: faith, hope, love)")
@click.option("--subthemes", help="Comma-separated weekly subthemes (optional)")
@click.option("--year", type=int, default=2026, help="Year to run demo for")
@click.option("--month", type=int, default=3, help="Month to run demo for (1-12)")
@click.option("--background-color", help="Override background color (e.g., #4A90E2)")
def demo(theme: str | None, subthemes: str | None, year: int, month: int, background_color: str | None) -> None:
    """Run demo with faith/hope/love concept.

    Example:
        demo
        demo --month 2
        demo --theme "My Theme" --year 2026 --month 2
        demo --theme "My Theme" --year 2026 --month 2 --subthemes "Week 1, Week 2"
    """
    if theme is None:
        theme = "The only three things that matter are faith, hope, and love, but the greatest of these is love."

    # Parse subthemes if provided
    weekly_subthemes_list = None
    if subthemes:
        weekly_subthemes_list = [s.strip() for s in subthemes.split(",")]

    # Call run-all with demo settings
    from click.testing import CliRunner

    runner = CliRunner()

    if weekly_subthemes_list:
        click.echo("✓ Running demo with provided weekly subthemes")
        args = ["--theme", theme, "--year", str(year), "--month", str(month), "--subthemes", subthemes]
    else:
        click.echo("✓ Running demo with AI-derived weekly subthemes")
        args = ["--theme", theme, "--year", str(year), "--month", str(month)]

    if background_color:
        args.extend(["--background-color", background_color])

    result = runner.invoke(run_all, args)

    # Show results
    if result.exit_code == 0:
        click.echo("\n✓ Demo completed!")
    else:
        click.echo(f"\n✗ Demo failed with exit code {result.exit_code}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
