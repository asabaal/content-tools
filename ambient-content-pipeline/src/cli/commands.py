"""CLI commands for the ambient content pipeline."""

import asyncio
import json
import sys
from pathlib import Path
from typing import cast

import click

from src.cli.preview import generate_preview
from src.ai_generator import generator
from src.config.defaults import (
    COLORFUL_PRESETS,
    DEFAULT_AI_MODEL,
    DEFAULT_TTS_VOICE,
    MAX_WORDS_PER_SLOT,
    AnimType,
    GradientDirection,
    TextureBlendMode,
    TextureType,
)
from src.errors.exceptions import (
    ModelUnavailableError,
    PipelineError,
)
from src.payload import schema, validation
from src.pipeline import orchestrator
from src.renderer import html_renderer
from src.slots.enum import SlotFunction
from src.weekly_calendar.resolver import resolve_calendar

WORKFLOW_ORDER = [
    "init-month",
    "validate",
    "resolve-calendar",
    "run-all",
    "demo",
    "preview",
    "regen-text",
    "inspect-plan",
    "rerender",
    "refine-posts",
    "list-presets",
    "show-preset",
]


class WorkflowGroup(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        return [cmd for cmd in WORKFLOW_ORDER if cmd in self.commands]

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        super().format_help(ctx, formatter)
        for cmd_name in self.list_commands(ctx):
            cmd = self.commands[cmd_name]
            sub_ctx = click.Context(cmd, info_name=cmd_name, parent=ctx)
            params = cmd.get_params(sub_ctx)
            opts = []
            for param in params:
                record = param.get_help_record(sub_ctx)
                if record:
                    opts.append(record)
            if opts:
                with formatter.section(cmd_name):
                    formatter.write_dl(opts)


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


@click.group(
    cls=WorkflowGroup,
    epilog="""\
Examples:
  acp run-all --animate --theme "Evolving in Christ" --year 2026 --month 2
  acp run-all --animate --payload 2026-02_payload.json
  acp demo
  acp rerender --plan-dir 202603 --all --background-color "#1a1a2e"\
""",
)
def cli() -> None:
    """ACP - Ambient Content Pipeline.

    Convert monthly themes into daily publishable images without requiring
    daily judgment.

    \b
    Workflow:
      1. init-month       Create a payload JSON for a month
      2. validate         Check your payload is correct
      3. run-all          Run the full pipeline (plan -> generate -> render)
      4. rerender         Re-render specific dates with different styles
      5. refine-posts     Iterate on posts with AI-assisted feedback

    \b
    Quick start:
      acp demo
      acp run-all --theme "..." --year 2026 --month 6
    """
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
@click.option(
    "--gradient-direction",
    type=click.Choice(
        [
            "vertical_top_bottom",
            "vertical_bottom_top",
            "horizontal_left_right",
            "horizontal_right_left",
            "diagonal_tl_br",
            "diagonal_tr_bl",
            "radial_center",
            "radial_top",
            "radial_bottom",
        ]
    ),
    help="Gradient direction",
)
@click.option(
    "--gradient-colors", help="Comma-separated hex colors for gradient (2-4, e.g., #FF0000,#00FF00)"
)
@click.option(
    "--gradient-stops", help="Comma-separated stop positions (0.0-1.0, e.g., 0.0,0.5,1.0)"
)
@click.option(
    "--texture-type",
    type=click.Choice(
        [
            "none",
            "noise_fine",
            "noise_coarse",
            "grain_film",
            "paper_subtle",
            "vignette_soft",
            "vignette_heavy",
        ]
    ),
    help="Texture overlay type",
)
@click.option("--texture-opacity", type=float, help="Texture opacity (0.0-1.0, default 0.15)")
@click.option(
    "--texture-blend-mode",
    type=click.Choice(["normal", "multiply", "overlay"]),
    help="Texture blend mode",
)
@click.option("--output-dir", "-o", help="Output directory for plans and images (default: outputs)")
@click.option("--animate", is_flag=True, help="Enable animate mode to produce video output")
@click.option(
    "--anim-type",
    type=click.Choice(["drift", "flow", "pulse", "distortion", "parallax", "reactive"]),
    help="Animation type (default: drift)",
)
@click.option("--anim-intensity", type=float, help="Animation intensity 0.0-0.5 (default: 0.2)")
@click.option("--anim-speed", type=float, help="Animation speed 0.1-2.0 (default: 1.0)")
@click.option("--anim-loop", type=int, help="Loop duration in seconds (default: 60)")
@click.option("--anim-seed", type=int, help="Seed for deterministic animation")
@click.option("--audio", is_flag=True, help="Generate TTS narration audio for animated videos")
@click.option("--audio-voice", help="Edge TTS voice name (default: en-US-AriaNeural)")
@click.option(
    "--text-color",
    help="Text color override (hex, e.g. #FFFFFF). Auto-computed from background if not set.",
)
@click.option("--bg-music", is_flag=True, help="Enable background music (implied by --animate)")
@click.option(
    "--bg-music-prompt", help="Music generation prompt. Auto-generated from theme if not set."
)
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
    gradient_direction: str | None,
    gradient_colors: str | None,
    gradient_stops: str | None,
    texture_type: str | None,
    texture_opacity: float | None,
    texture_blend_mode: str | None,
    output_dir: str | None,
    animate: bool,
    anim_type: str | None,
    anim_intensity: float | None,
    anim_speed: float | None,
    anim_loop: int | None,
    anim_seed: int | None,
    audio: bool,
    audio_voice: str | None,
    text_color: str | None,
    bg_music: bool,
    bg_music_prompt: str | None,
) -> None:
    """Run full pipeline: plan -> generate text -> render.

    \b
    Modes:
      Default      Static images
      --animate    Animated video with TTS narration + background music
                   (--audio and --bg-music are implied)

    \b
    Examples:
      acp run-all --payload 2026-06_payload.json
      acp run-all --animate --theme "Hope" --year 2026 --month 6
      acp run-all --animate --theme "Hope" --year 2026 --month 6 --subthemes "Wk1, Wk2"
      acp run-all --animate --payload month.json --bg-music-prompt "calm piano"
    """
    if animate:
        if not audio:
            audio = True
        if not bg_music:
            bg_music = True
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
        parsed_gradient_colors = (
            [c.strip() for c in gradient_colors.split(",")] if gradient_colors else None
        )
        parsed_gradient_stops = (
            [float(s.strip()) for s in gradient_stops.split(",")] if gradient_stops else None
        )

        results = asyncio.run(
            orchestrator.validate_and_run(
                str(payload_path),
                model=model,
                background_color=background_color,
                skip_rendering=skip_rendering,
                skip_text_generation=skip_text,
                output_dir=output_dir,
                gradient_direction=cast(GradientDirection | None, gradient_direction),
                gradient_colors=parsed_gradient_colors,
                gradient_stops=parsed_gradient_stops,
                texture_type=cast(TextureType | None, texture_type),
                texture_opacity=texture_opacity,
                texture_blend_mode=cast(TextureBlendMode | None, texture_blend_mode),
                animate=animate,
                anim_type=cast(AnimType | None, anim_type),
                anim_intensity=anim_intensity,
                anim_speed=anim_speed,
                anim_loop=anim_loop,
                anim_seed=anim_seed,
                audio=audio,
                audio_voice=audio_voice,
                text_color=text_color,
                bg_music=bg_music,
                bg_music_prompt=bg_music_prompt,
            )
        )

        # Summary
        click.echo(f"\n✓ Pipeline completed successfully!")
        click.echo(f"  Plan saved: {results['plan_path']}")
        click.echo(f"  Texts saved: {results['texts_path']}")
        if not skip_text:
            click.echo(f"  Generated texts: {len(results['generated_texts'])}")
        if not skip_rendering:
            if animate:
                click.echo(f"  Rendered videos: {len(results['rendered_images'])}")
            else:
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
@click.option("--plan-dir", help="Directory containing plans (e.g., outputs/202605)")
@click.option("--year", type=int, help="Year (alternative to --plan-dir)")
@click.option("--month", type=int, help="Month (alternative to --plan-dir)")
@click.option("--open", "open_browser", is_flag=True, help="Open the preview in your browser")
def preview(plan_dir: str | None, year: int | None, month: int | None, open_browser: bool) -> None:
    """Generate an HTML preview of all generated texts for a month.

    \b
    Examples:
      acp preview --plan-dir outputs/202605
      acp preview --year 2026 --month 5
      acp preview --year 2026 --month 5 --open
    """
    import webbrowser

    if plan_dir is None:
        if year is None or month is None:
            click.echo("✗ Provide --plan-dir or both --year and --month", err=True)
            sys.exit(1)
        plan_path = Path("outputs") / f"{year}{month:02d}"
        if not plan_path.exists():
            plan_path = Path("outputs")
    else:
        plan_path = Path(plan_dir)

    if not plan_path.exists():
        click.echo(f"✗ Directory not found: {plan_path}", err=True)
        sys.exit(1)

    try:
        output_path = generate_preview(plan_path, year=year, month=month)
        click.echo(f"✓ Preview generated: {output_path}")
        if open_browser:
            webbrowser.open(f"file://{output_path.resolve()}")
            click.echo("  Opened in browser.")
        else:
            click.echo(f"  Open with: file://{output_path.resolve()}")
    except FileNotFoundError as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--plan-dir", required=True, help="Directory containing plans (e.g., outputs)")
@click.option(
    "--dates",
    required=True,
    help="Comma-separated dates to regenerate (e.g., 2026-05-04,2026-05-05)",
)
@click.option("--model", help="Override AI model (e.g., qwen3.5:35b-a3b)")
@click.option("--temperature", type=float, help="Override AI temperature (0.0-1.0, default 0.2)")
@click.option("--preview", "gen_preview", is_flag=True, help="Regenerate preview HTML after")
def regen_text(plan_dir: str, dates: str, model: str | None, temperature: float | None, gen_preview: bool) -> None:
    """Regenerate text for specific dates using AI.

    Reads the existing plan and texts, regenerates only the specified dates,
    and saves the updated texts file. All other existing texts are passed
    as context to prevent repetition.

    \b
    Examples:
      acp regen-text --plan-dir outputs --dates 2026-05-04,2026-05-05
      acp regen-text --plan-dir outputs --dates 2026-05-04,2026-05-05 --preview
      acp regen-text --plan-dir outputs --dates 2026-05-04 --model qwen3.5:35b-a3b
    """
    plan_path = Path(plan_dir)
    plans_dir = plan_path / "plans"

    plan_files = sorted(
        [f for f in plans_dir.glob("*_plan.json") if not f.name.startswith("temp_")]
    )
    if not plan_files:
        click.echo(f"✗ No plan file found in {plans_dir}", err=True)
        sys.exit(1)

    texts_files = list(plans_dir.glob("*_texts.json"))
    if not texts_files:
        click.echo(f"✗ No texts file found in {plans_dir}", err=True)
        sys.exit(1)

    target_dates = [d.strip() for d in dates.split(",")]
    if not target_dates:
        click.echo("✗ No dates provided", err=True)
        sys.exit(1)

    first_date = target_dates[0]
    year_part, month_part = first_date.split("-")[0], first_date.split("-")[1]
    target_plan = f"{year_part}-{month_part}_plan.json"
    target_texts = f"{year_part}-{month_part}_texts.json"

    plan_match = [f for f in plan_files if f.name == target_plan]
    if not plan_match:
        click.echo(f"✗ No plan file for {year_part}-{month_part} in {plans_dir}", err=True)
        sys.exit(1)

    texts_match = [f for f in texts_files if f.name == target_texts]
    if not texts_match:
        click.echo(f"✗ No texts file for {year_part}-{month_part} in {plans_dir}", err=True)
        sys.exit(1)

    with open(plan_match[0], "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    with open(texts_match[0], "r", encoding="utf-8") as f:
        texts_data = json.load(f)

    generated_texts = texts_data.get("texts", {})
    slot_lookup = {slot["date"]: slot for slot in plan_data.get("schedule_summary", [])}
    monthly_theme = plan_data.get("monthly_theme", "")
    weekly_subtitles = plan_data.get("weekly_subtitles", {})

    invalid_dates = [d for d in target_dates if d not in slot_lookup]
    if invalid_dates:
        click.echo(f"✗ Dates not found in plan: {', '.join(invalid_dates)}", err=True)
        sys.exit(1)

    click.echo(f"Regenerating {len(target_dates)} posts...")

    async def do_regen():
        available = await generator.check_model_available()
        if not available:
            click.echo(
                f"✗ Model '{model or DEFAULT_AI_MODEL}' not found in Ollama.",
                err=True,
            )
            click.echo(f"  Please run: ollama pull {model or DEFAULT_AI_MODEL}")
            sys.exit(1)

        for date_str in target_dates:
            slot = slot_lookup[date_str]
            slot_type_str = slot["slot_type"]
            weekly_subtheme = slot.get("subtheme", "")

            try:
                slot_enum = SlotFunction(slot_type_str)
            except ValueError:
                click.echo(f"  ✗ Unknown slot type '{slot_type_str}' for {date_str}", err=True)
                continue

            max_words = MAX_WORDS_PER_SLOT.get(slot_type_str, 50)

            other_texts_with_context = [
                {
                    "date": k,
                    "slot_type": slot_lookup[k]["slot_type"] if k in slot_lookup else "?",
                    "text": v,
                }
                for k, v in generated_texts.items()
                if k != date_str and v
            ]

            old_text = generated_texts.get(date_str, "")

            if model:
                original_model = generator.DEFAULT_AI_MODEL
                generator.DEFAULT_AI_MODEL = model

            if temperature is not None:
                original_temp = generator.AI_TEMPERATURE
                generator.AI_TEMPERATURE = temperature

            try:
                new_text = await generator.generate_daily_text(
                    slot_type=slot_enum,
                    monthly_theme=monthly_theme,
                    weekly_subtheme=weekly_subtheme,
                    max_words=max_words,
                    previously_generated_with_context=other_texts_with_context,
                    current_date=date_str,
                )
            except Exception as e:
                click.echo(f"  ✗ Failed to regenerate {date_str}: {e}", err=True)
                continue
            finally:
                if model:
                    generator.DEFAULT_AI_MODEL = original_model
                if temperature is not None:
                    generator.AI_TEMPERATURE = original_temp

            generated_texts[date_str] = new_text

            click.echo(f"\n  {date_str} ({slot_type_str}):")
            click.echo(f"    OLD: {old_text[:80]}{'...' if len(old_text) > 80 else ''}")
            click.echo(f"    NEW: {new_text[:80]}{'...' if len(new_text) > 80 else ''}")

    asyncio.run(do_regen())

    with open(texts_match[0], "w", encoding="utf-8") as f:
        json.dump(texts_data, f, indent=2, ensure_ascii=False)
    click.echo(f"\n✓ Updated {len(target_dates)} posts in {texts_match[0]}")

    if gen_preview:
        try:
            output_path = generate_preview(
                plan_path,
                year=plan_data.get("year"),
                month=plan_data.get("month"),
            )
            click.echo(f"✓ Preview updated: {output_path}")
        except Exception as e:
            click.echo(f"  Warning: Preview generation failed: {e}", err=True)


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
        click.echo(f"  Week {i + 1}: {subtheme}")

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
def demo(
    theme: str | None, subthemes: str | None, year: int, month: int, background_color: str | None
) -> None:
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
        args = [
            "--theme",
            theme,
            "--year",
            str(year),
            "--month",
            str(month),
            "--subthemes",
            subthemes,
        ]
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
@click.option("--year", type=int, help="Year to select plan file (needed when plans/ has multiple months)")
@click.option("--month", type=int, help="Month to select plan file (needed when plans/ has multiple months)")
@click.option("--background-color", help="Override background color (e.g., #4A90E2)")
@click.option(
    "--gradient-direction",
    type=click.Choice(
        [
            "vertical_top_bottom",
            "vertical_bottom_top",
            "horizontal_left_right",
            "horizontal_right_left",
            "diagonal_tl_br",
            "diagonal_tr_bl",
            "radial_center",
            "radial_top",
            "radial_bottom",
        ]
    ),
    help="Gradient direction",
)
@click.option("--gradient-colors", help="Comma-separated hex colors for gradient (2-4)")
@click.option("--gradient-stops", help="Comma-separated stop positions (0.0-1.0)")
@click.option(
    "--texture-type",
    type=click.Choice(
        [
            "none",
            "noise_fine",
            "noise_coarse",
            "grain_film",
            "paper_subtle",
            "vignette_soft",
            "vignette_heavy",
        ]
    ),
    help="Texture overlay type",
)
@click.option("--texture-opacity", type=float, help="Texture opacity (0.0-1.0)")
@click.option(
    "--texture-blend-mode",
    type=click.Choice(["normal", "multiply", "overlay"]),
    help="Texture blend mode",
)
@click.option("--output-dir", "-o", help="Output directory for images (default: same as plan-dir)")
@click.option("--animate", is_flag=True, help="Enable animate mode to produce video output")
@click.option(
    "--anim-type",
    type=click.Choice(["drift", "flow", "pulse", "distortion", "parallax", "reactive"]),
    help="Animation type (default: drift)",
)
@click.option("--anim-intensity", type=float, help="Animation intensity 0.0-0.5 (default: 0.2)")
@click.option("--anim-speed", type=float, help="Animation speed 0.1-2.0 (default: 1.0)")
@click.option("--anim-loop", type=int, help="Loop duration in seconds (default: 60)")
@click.option("--anim-seed", type=int, help="Seed for deterministic animation")
@click.option("--audio", is_flag=True, help="Generate TTS narration audio for animated videos")
@click.option("--audio-voice", help="Edge TTS voice name (default: en-US-AriaNeural)")
@click.option(
    "--text-color",
    help="Text color override (hex, e.g. #FFFFFF). Auto-computed from background if not set.",
)
@click.option("--bg-music", is_flag=True, help="Enable background music (implied by --animate)")
@click.option("--bg-music-prompt", help="Music prompt to use when generating new music")
@click.option("--regen-music", is_flag=True, help="Force regeneration of background music")
def rerender(
    plan_dir: str,
    target_date: str | None,
    render_all: bool,
    year: int | None,
    month: int | None,
    background_color: str | None,
    gradient_direction: str | None,
    gradient_colors: str | None,
    gradient_stops: str | None,
    texture_type: str | None,
    texture_opacity: float | None,
    texture_blend_mode: str | None,
    output_dir: str | None,
    animate: bool,
    anim_type: str | None,
    anim_intensity: float | None,
    anim_speed: float | None,
    anim_loop: int | None,
    anim_seed: int | None,
    audio: bool,
    audio_voice: str | None,
    text_color: str | None,
    bg_music: bool,
    bg_music_prompt: str | None,
    regen_music: bool,
) -> None:
    """Re-render images (or videos) from a saved plan and texts.

    Reuses the style settings from the original run-all unless overridden.

    \b
    Examples:
      acp rerender --plan-dir 202603 --all
      acp rerender --plan-dir 202603 --date 2026-03-09
      acp rerender --plan-dir 202603 --all --background-color "#1a1a2e"
      acp rerender --plan-dir 202603 --all --animate
    """
    plan_path = Path(plan_dir) / "plans"

    # Find plan file
    plan_files = [f for f in plan_path.glob("*_plan.json") if not f.name.startswith("temp_")]
    if not plan_files:
        click.echo(f"✗ No plan file found in {plan_path}", err=True)
        sys.exit(1)

    if year is not None and month is not None:
        target_plan = f"{year}-{month:02d}_plan.json"
        target_texts_name = f"{year}-{month:02d}_texts.json"
        plan_match = [f for f in plan_files if f.name == target_plan]
        if not plan_match:
            click.echo(f"✗ No plan file for {year}-{month:02d} in {plan_path}", err=True)
            sys.exit(1)
        plan_file = plan_match[0]
    else:
        plan_file = plan_files[0]

    # Find texts file
    texts_files = list(plan_path.glob("*_texts.json"))
    if not texts_files:
        click.echo(f"✗ No texts file found in {plan_path}", err=True)
        sys.exit(1)

    if year is not None and month is not None:
        texts_match = [f for f in texts_files if f.name == target_texts_name]
        if not texts_match:
            click.echo(f"✗ No texts file for {year}-{month:02d} in {plan_path}", err=True)
            sys.exit(1)
        texts_file = texts_match[0]
    else:
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

    parsed_gradient_colors = (
        [c.strip() for c in gradient_colors.split(",")] if gradient_colors else None
    )
    parsed_gradient_stops = (
        [float(s.strip()) for s in gradient_stops.split(",")] if gradient_stops else None
    )
    effective_gradient_direction = cast(GradientDirection | None, gradient_direction) or cast(
        GradientDirection | None, stored_render_config.get("gradient_direction")
    )
    effective_gradient_colors = parsed_gradient_colors or stored_render_config.get(
        "gradient_colors"
    )
    effective_gradient_stops = parsed_gradient_stops or stored_render_config.get("gradient_stops")
    effective_texture_type = cast(TextureType | None, texture_type) or cast(
        TextureType | None, stored_render_config.get("texture_type")
    )
    effective_texture_opacity = (
        texture_opacity
        if texture_opacity is not None
        else stored_render_config.get("texture_opacity")
    )
    effective_texture_blend = cast(TextureBlendMode | None, texture_blend_mode) or cast(
        TextureBlendMode | None, stored_render_config.get("texture_blend_mode")
    )

    effective_animate = animate or stored_render_config.get("animate", False)
    if effective_animate:
        if not audio:
            audio = True
    effective_anim_type = cast(AnimType | None, anim_type) or cast(
        AnimType | None, stored_render_config.get("anim_type")
    )
    effective_anim_intensity = (
        anim_intensity if anim_intensity is not None else stored_render_config.get("anim_intensity")
    )
    effective_anim_speed = (
        anim_speed if anim_speed is not None else stored_render_config.get("anim_speed")
    )
    effective_anim_loop = (
        anim_loop if anim_loop is not None else stored_render_config.get("anim_loop")
    )
    effective_anim_seed = (
        anim_seed if anim_seed is not None else stored_render_config.get("anim_seed")
    )

    saved_music_path = stored_render_config.get("bg_music_path")
    saved_music_prompt = stored_render_config.get("bg_music_prompt")
    effective_bg_music = bg_music or bool(saved_music_path) or effective_animate
    effective_music_path: str | None = None
    need_generate_music = False

    if effective_bg_music:
        effective_animate = True
        if regen_music:
            need_generate_music = True
        elif saved_music_path and not bg_music_prompt:
            import os

            if os.path.exists(saved_music_path):
                effective_music_path = saved_music_path
            else:
                need_generate_music = True
                click.echo("  Warning: Saved music file not found, will regenerate")
        elif bg_music_prompt:
            need_generate_music = True
        else:
            effective_bg_music = False
            click.echo("  Warning: No music available. Use --regen-music or --bg-music-prompt.")

    # Determine output directory
    images_dir = Path(output_dir) / "images" if output_dir else Path(plan_dir) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Determine which dates to render
    if render_all:
        dates_to_render = [
            slot["date"] for slot in plan_data["schedule_summary"] if slot["is_automated"]
        ]
    elif target_date:
        dates_to_render = [target_date]
    else:
        click.echo("✗ Must specify --date or --all", err=True)
        sys.exit(1)

    # Build slot lookup from schedule_summary
    slot_lookup = {slot["date"]: slot for slot in plan_data["schedule_summary"]}

    # Get weekly subtitles
    weekly_subtitles = plan_data.get("weekly_subtitles", {})

    rerender_tts_paths: dict[str, str] = {}
    rerender_tts_durations: dict[str, float] = {}

    async def generate_music_if_needed():
        nonlocal effective_music_path

        if not need_generate_music:
            return

        import tempfile

        from src.renderer.music_gen import (
            calculate_music_duration,
            generate_background_music,
            generate_music_prompt_from_theme,
        )
        from src.renderer.tts import generate_tts, get_audio_duration

        prompt = bg_music_prompt or saved_music_prompt
        if not prompt:
            prompt = await generate_music_prompt_from_theme(plan_data["monthly_theme"])
            click.echo(f"  Auto-generated music prompt: {prompt}")

        max_tts = 0.0
        click.echo(f"  Generating TTS audio for {len(dates_to_render)} posts...")
        for i, date in enumerate(dates_to_render, 1):
            text = generated_texts.get(date, "")
            if text:
                click.echo(f"    [{i}/{len(dates_to_render)}] {date}")
                tts_tmp = tempfile.NamedTemporaryFile(
                    suffix=".mp3", delete=False, dir=str(images_dir)
                )
                tts_tmp.close()
                await generate_tts(
                    text=text,
                    output_path=tts_tmp.name,
                    voice=audio_voice or DEFAULT_TTS_VOICE,
                )
                dur = get_audio_duration(tts_tmp.name)
                rerender_tts_paths[date] = tts_tmp.name
                rerender_tts_durations[date] = dur
                max_tts = max(max_tts, dur)
        click.echo(f"  TTS complete. Longest narration: {max_tts:.1f}s")

        music_dur = calculate_music_duration(max_tts) if max_tts > 0 else 15.0
        audio_dir = images_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        music_out = str(audio_dir / "bg_music.wav")

        click.echo(f"  Generating music: {prompt}")
        click.echo(f"  Duration: {music_dur:.1f}s")
        effective_music_path = await generate_background_music(
            prompt=prompt,
            duration=music_dur,
            output_path=music_out,
        )
        click.echo(f"  Music saved: {effective_music_path}")

        import json as _json

        with open(plan_file, "r", encoding="utf-8") as f:
            plan_update = _json.load(f)
        plan_update["render_config"]["bg_music"] = True
        plan_update["render_config"]["bg_music_prompt"] = prompt
        plan_update["render_config"]["bg_music_path"] = effective_music_path
        with open(plan_file, "w", encoding="utf-8") as f:
            _json.dump(plan_update, f, indent=2, ensure_ascii=False)

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

            if effective_animate:
                output_path = html_renderer.get_video_output_path(
                    year=year,
                    month=month,
                    day=day,
                    monthly_theme=plan_data["monthly_theme"],
                    week_number=slot.get("week_number", 1),
                    subtheme=weekly_subtitles.get(
                        slot.get("week_number", 1), slot.get("subtheme", "")
                    ),
                    slot_type=slot["slot_type"],
                    images_dir=images_dir,
                )
            else:
                output_path = html_renderer.get_output_path(
                    year=year,
                    month=month,
                    day=day,
                    monthly_theme=plan_data["monthly_theme"],
                    week_number=slot.get("week_number", 1),
                    subtheme=weekly_subtitles.get(
                        slot.get("week_number", 1), slot.get("subtheme", "")
                    ),
                    slot_type=slot["slot_type"],
                    images_dir=images_dir,
                )

            try:
                if effective_animate:
                    click.echo(f"  [{rendered + 1}/{len(dates_to_render)}] Rendering {date} ({slot['slot_type']})...")
                    audio_path = None
                    video_dur = None

                    if effective_bg_music and effective_music_path and text:
                        import tempfile

                        from src.renderer.audio_mix import prepare_slot_audio
                        from src.renderer.music_gen import calculate_slot_video_duration

                        if date in rerender_tts_paths:
                            slot_tts_path = rerender_tts_paths[date]
                            tts_dur = rerender_tts_durations[date]
                        else:
                            from src.renderer.tts import generate_tts, get_audio_duration

                            tts_tmp = tempfile.NamedTemporaryFile(
                                suffix=".mp3", delete=False, dir=str(images_dir)
                            )
                            tts_tmp.close()
                            click.echo(f"  Generating TTS audio for {date}...")
                            await generate_tts(
                                text=text,
                                output_path=tts_tmp.name,
                                voice=audio_voice or DEFAULT_TTS_VOICE,
                            )
                            slot_tts_path = tts_tmp.name
                            tts_dur = get_audio_duration(tts_tmp.name)

                        slot_video_dur = calculate_slot_video_duration(tts_dur)

                        mixed_tmp = tempfile.NamedTemporaryFile(
                            suffix=".mp3", delete=False, dir=str(images_dir)
                        )
                        mixed_tmp.close()
                        click.echo(f"    Mixing audio with background music...")
                        audio_path, video_dur = prepare_slot_audio(
                            tts_path=slot_tts_path,
                            music_path=effective_music_path,
                            output_path=mixed_tmp.name,
                            tts_duration=tts_dur,
                            slot_video_duration=slot_video_dur,
                        )

                    elif audio and text:
                        import tempfile

                        from src.renderer.tts import generate_tts

                        audio_tmp = tempfile.NamedTemporaryFile(
                            suffix=".mp3", delete=False, dir=str(images_dir)
                        )
                        audio_tmp.close()
                        audio_path = audio_tmp.name
                        click.echo(f"  Generating TTS audio...")
                        await generate_tts(
                            text=text,
                            output_path=audio_path,
                            voice=audio_voice or DEFAULT_TTS_VOICE,
                        )

                    await html_renderer.render_animated_video(
                        text=text,
                        slot_info=slot_info,
                        output_path=output_path,
                        style_preset=stored_style_preset,
                        background_color=effective_bg_color,
                        gradient_direction=effective_gradient_direction,
                        gradient_colors=effective_gradient_colors,
                        gradient_stops=effective_gradient_stops,
                        texture_type=effective_texture_type,
                        texture_opacity=effective_texture_opacity,
                        texture_blend_mode=effective_texture_blend,
                        anim_type=effective_anim_type or "drift",
                        anim_intensity=effective_anim_intensity
                        if effective_anim_intensity is not None
                        else 0.2,
                        anim_speed=effective_anim_speed
                        if effective_anim_speed is not None
                        else 1.0,
                        anim_loop=effective_anim_loop if effective_anim_loop is not None else 60,
                        anim_seed=effective_anim_seed,
                        audio_path=audio_path,
                        text_color=text_color,
                        video_duration=video_dur,
                    )
                else:
                    await html_renderer.render_text_to_image(
                        text=text,
                        slot_info=slot_info,
                        output_path=output_path,
                        style_preset=stored_style_preset,
                        background_color=effective_bg_color,
                        gradient_direction=effective_gradient_direction,
                        gradient_colors=effective_gradient_colors,
                        gradient_stops=effective_gradient_stops,
                        texture_type=effective_texture_type,
                        texture_opacity=effective_texture_opacity,
                        texture_blend_mode=effective_texture_blend,
                        text_color=text_color,
                    )
                click.echo(f"  Rendered: {output_path}")
                rendered += 1
            except Exception as e:
                click.echo(f"  Warning: Failed to render {date}: {e}")

        return rendered

    label = "video(s)" if effective_animate else "image(s)"
    click.echo(f"Re-rendering {len(dates_to_render)} {label}...")

    async def run_all():
        await generate_music_if_needed()
        return await do_render()

    rendered_count = asyncio.run(run_all())
    click.echo(f"\n✓ Rendered {rendered_count} {label}")


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
        raise ValueError(
            "No valid feedback entries found. Expected format: DATE::feedback|DATE::feedback"
        )
    return entries


@cli.command()
@click.option("--plan-dir", required=True, help="Directory containing plans (e.g., 202604-draft)")
@click.option("--feedback", required=True, help="Feedback string: DATE::feedback|DATE::feedback")
def refine_posts(plan_dir: str, feedback: str) -> None:
    """Refine existing posts with user feedback.

    Example:
        acp refine-posts --plan-dir 202604-draft --feedback "2026-04-05::Too generic."
        acp refine-posts --plan-dir 202604-draft --feedback "2026-04-05::Too generic.|2026-04-12::Too abstract."
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
            click.echo(f"\n{'#' * 60}")
            click.echo(f"Entry {entry_index}/{len(parsed_entries)}: {target_date}")
            click.echo(f"{'#' * 60}")

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
                click.echo(f"\n{'=' * 50}")
                click.echo(f"Date: {target_date}")
                click.echo(f"Slot type: {slot_type}")
                click.echo(f"\nCurrent post:\n  {current_post}")
                click.echo(f"\nFeedback:\n  {accumulated_feedback}")
                click.echo(f"{'=' * 50}")

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
                        "subtheme_subtitle": weekly_subtitles.get(
                            slot_info.get("week_number", 1), ""
                        ),
                        "monthly_theme": monthly_theme,
                    }
                    render_output_path = html_renderer.get_output_path(
                        year=year,
                        month=month,
                        day=day,
                        monthly_theme=monthly_theme,
                        week_number=slot_info.get("week_number", 1),
                        subtheme=weekly_subtitles.get(
                            slot_info.get("week_number", 1), slot_info.get("subtheme", "")
                        ),
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

    click.echo(f"\n{'#' * 60}")
    if early_exit:
        click.echo(f"⊗ Exited early. Processed: {processed_count}, Skipped: {skipped_count}")
    else:
        click.echo(f"✓ Completed. Processed: {processed_count}, Skipped: {skipped_count}")
    click.echo(f"{'#' * 60}")


if __name__ == "__main__":  # pragma: no cover
    cli()
