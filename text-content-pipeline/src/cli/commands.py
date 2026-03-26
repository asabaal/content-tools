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
    MAX_WORDS_PER_SLOT,
)
from src.errors.exceptions import (
    ModelUnavailableError,
    PipelineError,
)
from src.payload import schema, validation
from src.pipeline import orchestrator
from src.renderer import html_renderer


REFINEMENT_PROMPT = """You are refining a social media post based on user feedback.

Monthly theme: {monthly_theme}
Weekly subtheme: {weekly_subtheme}
Slot type: {slot_type}

Original post:
{original_post}

User feedback:
{feedback}

Task: Rewrite the post to address the user feedback while staying true to the monthly theme, weekly subtheme, and slot type requirements.

Requirements:
- Directly address the feedback provided
- Maintain consistency with the theme and subtheme
- Follow the slot type format ({slot_type})
- Plain text only (no markdown, no emojis, no hashtags)
- Maximum {max_words} words

Output: Just the refined post, nothing else."""


@click.group()
def cli() -> None:
    """Text content pipeline - Convert monthly themes into daily images."""
    pass  # pragma: no cover


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
@click.option("--output-dir", "-o", help="Output directory for plans and images (default: outputs)")
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
    output_dir: str | None,
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
                output_dir=output_dir,
            )
        )

        # Summary
        click.echo(f"\n✓ Pipeline completed successfully!")
        click.echo(f"  Plan saved: {results['plan_path']}")
        click.echo(f"  Texts saved: {results['texts_path']}")
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


@cli.command()
@click.option("--plan-dir", required=True, help="Directory containing plans (e.g., 202603)")
@click.option("--date", "target_date", help="Specific date to re-render (e.g., 2026-03-09)")
@click.option("--all", "render_all", is_flag=True, help="Re-render all dates")
@click.option("--background-color", help="Override background color (e.g., #4A90E2)")
@click.option("--output-dir", "-o", help="Output directory for images (default: same as plan-dir)")
def rerender(
    plan_dir: str,
    target_date: str | None,
    render_all: bool,
    background_color: str | None,
    output_dir: str | None,
) -> None:
    """Re-render images from saved plan and texts.

    Example:
        tcp rerender --plan-dir 202603 --date 2026-03-09
        tcp rerender --plan-dir 202603 --all
        tcp rerender --plan-dir 202603 --date 2026-03-09 --background-color "#ff0000"
    """
    plan_path = Path(plan_dir) / "plans"

    # Find plan file
    plan_files = list(plan_path.glob("*_plan.json"))
    if not plan_files:
        click.echo(f"✗ No plan file found in {plan_path}", err=True)
        sys.exit(1)
    plan_file = plan_files[0]

    # Find texts file
    texts_files = list(plan_path.glob("*_texts.json"))
    if not texts_files:
        click.echo(f"✗ No texts file found in {plan_path}", err=True)
        sys.exit(1)
    texts_file = texts_files[0]

    # Load plan
    with open(plan_file, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    # Load texts
    with open(texts_file, "r", encoding="utf-8") as f:
        texts_data = json.load(f)

    generated_texts = texts_data.get("texts", {})

    # Read render config from plan (CLI --background-color overrides if provided)
    stored_render_config = plan_data.get("render_config", {})
    stored_style_preset = stored_render_config.get("style_preset", "default")
    stored_bg_color = stored_render_config.get("background_color")
    effective_bg_color = background_color or stored_bg_color

    # Determine output directory
    images_dir = Path(output_dir) / "images" if output_dir else Path(plan_dir) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Determine which dates to render
    if render_all:
        dates_to_render = [slot["date"] for slot in plan_data["schedule_summary"] if slot["is_automated"]]
    elif target_date:
        dates_to_render = [target_date]
    else:
        click.echo("✗ Must specify --date or --all", err=True)
        sys.exit(1)

    # Build slot lookup from schedule_summary
    slot_lookup = {slot["date"]: slot for slot in plan_data["schedule_summary"]}

    # Get weekly subtitles
    weekly_subtitles = plan_data.get("weekly_subtitles", {})

    async def do_render():
        rendered = 0
        for date in dates_to_render:
            if date not in slot_lookup:
                click.echo(f"  Warning: No slot found for {date}")
                continue

            slot = slot_lookup[date]
            text = generated_texts.get(date, "")

            if not text:
                click.echo(f"  Warning: No text for {date}")
                continue

            year, month, day = map(int, date.split("-"))

            slot_info = {
                "type": slot["slot_type"],
                "year": year,
                "month": month,
                "day": day,
                "week_number": str(slot.get("week_number", 1)),
                "subtheme": slot.get("subtheme", ""),
                "subtheme_subtitle": weekly_subtitles.get(slot.get("week_number", 1), ""),
                "monthly_theme": plan_data["monthly_theme"],
            }

            output_path = html_renderer.get_output_path(
                year=year,
                month=month,
                day=day,
                monthly_theme=plan_data["monthly_theme"],
                week_number=slot.get("week_number", 1),
                subtheme=weekly_subtitles.get(slot.get("week_number", 1), slot.get("subtheme", "")),
                slot_type=slot["slot_type"],
                images_dir=images_dir,
            )

            try:
                await html_renderer.render_text_to_image(
                    text=text,
                    slot_info=slot_info,
                    output_path=output_path,
                    style_preset=stored_style_preset,
                    background_color=effective_bg_color,
                )
                click.echo(f"  Rendered: {output_path}")
                rendered += 1
            except Exception as e:
                click.echo(f"  Warning: Failed to render {date}: {e}")

        return rendered

    click.echo(f"Re-rendering {len(dates_to_render)} image(s)...")
    rendered_count = asyncio.run(do_render())
    click.echo(f"\n✓ Rendered {rendered_count} image(s)")


async def _refine_post_with_ai(
    original_post: str,
    feedback: str,
    slot_type: str,
    monthly_theme: str,
    weekly_subtheme: str,
    max_words: int = 50,
) -> str:
    """Refine a post using AI based on user feedback."""
    prompt = REFINEMENT_PROMPT.format(
        original_post=original_post,
        feedback=feedback,
        slot_type=slot_type,
        monthly_theme=monthly_theme,
        weekly_subtheme=weekly_subtheme,
        max_words=max_words,
    )
    return await generator._call_ollama(prompt, touchpoint="post_refinement")


def _parse_feedback(feedback: str) -> list[tuple[str, str]]:
    """Parse feedback string into list of (date, feedback) tuples.

    Format: "DATE::feedback|DATE::feedback|..."
    """
    entries = []
    for entry in feedback.split("|"):
        entry = entry.strip()
        if not entry:
            continue
        if "::" not in entry:
            raise ValueError(f"Invalid feedback entry '{entry}'. Expected format: DATE::feedback")
        parts = entry.split("::", 1)
        date_str = parts[0].strip()
        feedback_text = parts[1].strip()
        if not date_str or not feedback_text:
            raise ValueError(f"Invalid feedback entry '{entry}'. Expected format: DATE::feedback")
        entries.append((date_str, feedback_text))
    if not entries:
        raise ValueError("No valid feedback entries found. Expected format: DATE::feedback|DATE::feedback")
    return entries


@cli.command()
@click.option("--plan-dir", required=True, help="Directory containing plans (e.g., 202604-draft)")
@click.option("--feedback", required=True, help="Feedback string: DATE::feedback|DATE::feedback")
def refine_posts(plan_dir: str, feedback: str) -> None:
    """Refine existing posts with user feedback.

    Example:
        tcp refine-posts --plan-dir 202604-draft --feedback "2026-04-05::Too generic."
        tcp refine-posts --plan-dir 202604-draft --feedback "2026-04-05::Too generic.|2026-04-12::Too abstract."
    """
    try:
        parsed_entries = _parse_feedback(feedback)
    except ValueError as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)

    click.echo(f"Parsed {len(parsed_entries)} feedback entries")

    plan_path = Path(plan_dir) / "plans"
    plan_files = list(plan_path.glob("*_plan.json"))
    if not plan_files:
        click.echo(f"✗ No plan file found in {plan_path}", err=True)
        sys.exit(1)
    plan_file = plan_files[0]

    texts_files = list(plan_path.glob("*_texts.json"))
    if not texts_files:
        click.echo(f"✗ No texts file found in {plan_path}", err=True)
        sys.exit(1)
    texts_file = texts_files[0]

    with open(plan_file, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    with open(texts_file, "r", encoding="utf-8") as f:
        texts_data = json.load(f)

    generated_texts = texts_data.get("texts", {})
    slot_lookup = {slot["date"]: slot for slot in plan_data.get("schedule_summary", [])}
    monthly_theme = plan_data.get("monthly_theme", "")
    weekly_subtitles = plan_data.get("weekly_subtitles", {})
    render_config = plan_data.get("render_config", {})
    style_preset = render_config.get("style_preset", "default")
    bg_color = render_config.get("background_color")
    images_dir = Path(plan_dir) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    skipped_count = 0

    async def process_all_entries():
        nonlocal processed_count, skipped_count
        
        for entry_index, (target_date, initial_feedback) in enumerate(parsed_entries, 1):
            click.echo(f"\n{'#'*60}")
            click.echo(f"Entry {entry_index}/{len(parsed_entries)}: {target_date}")
            click.echo(f"{'#'*60}")

            if target_date not in generated_texts:
                click.echo(f"✗ No post found for date: {target_date}, skipping", err=True)
                skipped_count += 1
                continue

            slot_info = slot_lookup.get(target_date, {})
            slot_type = slot_info.get("slot_type", "declarative_statement")
            max_words = MAX_WORDS_PER_SLOT.get(slot_type, 50)
            weekly_subtheme = slot_info.get("subtheme", "")

            current_post = generated_texts[target_date]
            accumulated_feedback = initial_feedback

            while True:
                click.echo(f"\n{'='*50}")
                click.echo(f"Date: {target_date}")
                click.echo(f"Slot type: {slot_type}")
                click.echo(f"\nCurrent post:\n  {current_post}")
                click.echo(f"\nFeedback:\n  {accumulated_feedback}")
                click.echo(f"{'='*50}")

                click.echo("\nGenerating refined post...")
                try:
                    revised_post = await _refine_post_with_ai(
                        original_post=current_post,
                        feedback=accumulated_feedback,
                        slot_type=slot_type,
                        monthly_theme=monthly_theme,
                        weekly_subtheme=weekly_subtheme,
                        max_words=max_words,
                    )
                    revised_post = revised_post.strip()
                except Exception as e:
                    click.echo(f"✗ AI refinement failed: {e}", err=True)
                    skipped_count += 1
                    break

                click.echo(f"\nRevised post:\n  {revised_post}")

                choice = click.prompt(
                    "\nOptions: 1=accept, 2=refine, 3=skip, 4=exit",
                    type=click.Choice(["1", "2", "3", "4"]),
                    default="1",
                )

                if choice == "1":
                    generated_texts[target_date] = revised_post
                    with open(texts_file, "w", encoding="utf-8") as f:
                        json.dump(texts_data, f, indent=2, ensure_ascii=False)
                    click.echo(f"\n✓ Post updated for {target_date}")

                    year, month, day = map(int, target_date.split("-"))
                    render_slot_info = {
                        "type": slot_type,
                        "year": year,
                        "month": month,
                        "day": day,
                        "week_number": str(slot_info.get("week_number", 1)),
                        "subtheme": slot_info.get("subtheme", ""),
                        "subtheme_subtitle": weekly_subtitles.get(slot_info.get("week_number", 1), ""),
                        "monthly_theme": monthly_theme,
                    }
                    render_output_path = html_renderer.get_output_path(
                        year=year,
                        month=month,
                        day=day,
                        monthly_theme=monthly_theme,
                        week_number=slot_info.get("week_number", 1),
                        subtheme=weekly_subtitles.get(slot_info.get("week_number", 1), slot_info.get("subtheme", "")),
                        slot_type=slot_type,
                        images_dir=images_dir,
                    )
                    try:
                        await html_renderer.render_text_to_image(
                            text=revised_post,
                            slot_info=render_slot_info,
                            output_path=render_output_path,
                            style_preset=style_preset,
                            background_color=bg_color,
                        )
                        click.echo(f"  Rendered: {render_output_path}")
                    except Exception as e:
                        click.echo(f"  Warning: Failed to render {target_date}: {e}")

                    processed_count += 1
                    break
                elif choice == "2":
                    additional_feedback = click.prompt("Enter additional feedback", type=str)
                    accumulated_feedback = f"{accumulated_feedback} {additional_feedback}"
                    current_post = revised_post
                    continue
                elif choice == "3":
                    click.echo(f"\n⊗ Skipped {target_date}")
                    skipped_count += 1
                    break
                elif choice == "4":
                    click.echo("\n✗ Exiting. No more entries processed.")
                    return True

        return False

    early_exit = asyncio.run(process_all_entries())

    click.echo(f"\n{'#'*60}")
    if early_exit:
        click.echo(f"⊗ Exited early. Processed: {processed_count}, Skipped: {skipped_count}")
    else:
        click.echo(f"✓ Completed. Processed: {processed_count}, Skipped: {skipped_count}")
    click.echo(f"{'#'*60}")


if __name__ == "__main__":  # pragma: no cover
    cli()
