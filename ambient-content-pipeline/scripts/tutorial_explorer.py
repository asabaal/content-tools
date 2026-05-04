"""ACP Tutorial Explorer - generates an interactive HTML gallery showing every visual option.

Usage:
    cd /mnt/storage/repos/content-tools/ambient-content-pipeline
    python scripts/tutorial_explorer.py

Outputs:
    tutorial.html          - open in browser
    tutorial_assets/       - generated images, videos, audio
"""

import asyncio
import base64
import io
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.defaults import (
    ACE_STEP_DEFAULT_GUIDANCE,
    ACE_STEP_DEFAULT_STEPS,
    ACE_STEP_MUSIC_VOLUME,
    ACE_STEP_TAIL_MAX,
    ACE_STEP_TAIL_RATIO,
    ACE_STEP_TTS_DELAY,
    ANIM_FPS,
    COLORFUL_PRESETS,
    DEFAULT_ANIM_LOOP,
    DEFAULT_TTS_VOICE,
    GradientDirection,
    TextureBlendMode,
    TextureType,
    AnimType,
    auto_contrast_color,
    companion_color,
)
from src.renderer.animation import AnimationFrameGenerator
from src.renderer.template_builder import build_html
from src.renderer.video_encoder import VideoEncoder

THUMB_SIZE = 540
VIDEO_DURATION = 8
VIDEO_FPS = 24

SAMPLE_TEXT = "The only three things that matter are faith, hope, and love, but the greatest of these is love."

SLOT_SAMPLE_TEXTS = {
    "declarative_statement": "Love does not require understanding to be real.",
    "excerpt": "I have been driven many times upon my knees by the overwhelming conviction that I had nowhere else to go. My own wisdom, and that of all about me, seemed insufficient for the day.",
    "process_note": "There is a slow work happening beneath the surface of things. Not everything that grows is visible. The seed resists its own breaking, yet the breaking is the beginning. I am learning to sit with the tension between what is and what is becoming.",
    "unanswered_question": "What would change if I stopped trying to earn what is already freely given?",
    "reframing": "Weakness is not the absence of strength — it is the ground where something else takes root.",
    "quiet_observation": "The light shifts differently through the window in late afternoon. Everything looks softer, as if the day itself is exhaling.",
}

SLOT_MAX_WORDS = {
    "declarative_statement": 25,
    "excerpt": 60,
    "process_note": 90,
    "unanswered_question": 20,
    "reframing": 25,
    "quiet_observation": 30,
}

SLOT_COLORS = {
    "declarative_statement": "#3B82F6",
    "excerpt": "#10B981",
    "process_note": "#F59E0B",
    "unanswered_question": "#8B5CF6",
    "reframing": "#EF4444",
    "quiet_observation": "#14B8A6",
    "human_intentional": "#6B7280",
}

BASE_SLOT_INFO = {
    "year": "2026",
    "month": "5",
    "day": "11",
    "week_number": "2",
    "subtheme": "Hope",
    "subtheme_subtitle": "The Quiet Anchor",
    "monthly_theme": "The only three things that matter are faith, hope, and love.",
}

ASSETS_DIR = PROJECT_ROOT / "tutorial_assets"
STATIC_DIR = ASSETS_DIR / "static"
VIDEO_DIR = ASSETS_DIR / "video"
AUDIO_DIR = ASSETS_DIR / "audio"
OUTPUT_HTML = PROJECT_ROOT / "tutorial.html"

ALL_GRADIENT_DIRECTIONS: list[GradientDirection] = [
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

ALL_TEXTURE_TYPES: list[TextureType] = [
    "none",
    "noise_fine",
    "noise_coarse",
    "grain_film",
    "paper_subtle",
    "vignette_soft",
    "vignette_heavy",
]

ALL_ANIM_TYPES: list[AnimType] = [
    "drift",
    "flow",
    "pulse",
    "distortion",
    "parallax",
]


def _log(msg: str) -> None:
    print(f"  [{time.strftime('%H:%M:%S')}] {msg}")


def _build_preset_card_html(
    text: str,
    slot_info: dict[str, str],
    preset_name: str = "default",
    background_color: str | None = None,
    gradient_direction: GradientDirection | None = None,
    gradient_colors: list[str] | None = None,
    gradient_stops: list[float] | None = None,
    texture_type: TextureType | None = None,
    texture_opacity: float | None = None,
    texture_blend_mode: TextureBlendMode | None = None,
    text_color: str | None = None,
) -> str:
    preset = COLORFUL_PRESETS.get(preset_name, COLORFUL_PRESETS["default"]).copy()
    if background_color:
        preset["background"] = background_color
    html = build_html(
        text=text,
        slot_info=slot_info,
        preset=preset,
        max_width=1080,
        max_height=1080,
        gradient_direction=gradient_direction,
        gradient_colors=gradient_colors,
        gradient_stops=gradient_stops,
        texture_type=texture_type,
        texture_opacity=texture_opacity,
        texture_blend_mode=texture_blend_mode,
        text_color=text_color,
    )
    return html


async def _render_html_to_png(html_content: str, output_path: Path, size: int = THUMB_SIZE) -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            page = await browser.new_page(viewport={"width": 1080, "height": 1080})
            await page.set_content(html_content)
            await page.screenshot(path=str(output_path), full_page=False)
        finally:
            await browser.close()
    return str(output_path)


async def generate_static_variants(progress: dict) -> None:
    _log("Generating static image variants...")

    if not STATIC_DIR.exists():
        STATIC_DIR.mkdir(parents=True)

    renders: list[tuple[str, str, str]] = []

    # --- Base post ---
    html = _build_preset_card_html(SAMPLE_TEXT, BASE_SLOT_INFO)
    renders.append(("base_default", html, "The Base Post — default blue, no options"))

    # --- Presets ---
    for name in COLORFUL_PRESETS:
        html = _build_preset_card_html(SAMPLE_TEXT, BASE_SLOT_INFO, preset_name=name)
        bg = COLORFUL_PRESETS[name]["background"]
        renders.append((f"preset_{name}", html, f"Preset: {name} ({bg})"))

    # --- Custom background colors ---
    custom_colors = [
        ("#1A1A2E", "Dark Navy"),
        ("#F5E6CC", "Warm Cream"),
        ("#2D2D2D", "Charcoal"),
        ("#E8D5B7", "Parchment"),
    ]
    for color, label in custom_colors:
        html = _build_preset_card_html(SAMPLE_TEXT, BASE_SLOT_INFO, background_color=color)
        renders.append((f"bg_{color.lstrip('#')}", html, f"Custom BG: {label} ({color})"))

    # --- Gradients ---
    base_bg = COLORFUL_PRESETS["default"]["background"]
    companion = companion_color(base_bg)

    for direction in ALL_GRADIENT_DIRECTIONS:
        html = _build_preset_card_html(
            SAMPLE_TEXT, BASE_SLOT_INFO,
            gradient_direction=direction,
            gradient_colors=[base_bg, companion],
        )
        renders.append((f"grad_{direction}", html, f"Gradient: {direction}"))

    three_color = [base_bg, companion_color(base_bg, 80), companion_color(base_bg, 160)]
    html = _build_preset_card_html(
        SAMPLE_TEXT, BASE_SLOT_INFO,
        gradient_direction="diagonal_tl_br",
        gradient_colors=three_color,
    )
    renders.append(("grad_3color", html, "Gradient: 3-color diagonal"))

    four_color = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
    html = _build_preset_card_html(
        SAMPLE_TEXT, BASE_SLOT_INFO,
        gradient_direction="diagonal_tl_br",
        gradient_colors=four_color,
        gradient_stops=[0.0, 0.3, 0.7, 1.0],
    )
    renders.append(("grad_4color", html, "Gradient: 4-color with custom stops"))

    # --- Textures ---
    for tex in ALL_TEXTURE_TYPES:
        html = _build_preset_card_html(
            SAMPLE_TEXT, BASE_SLOT_INFO,
            texture_type=tex,
        )
        renders.append((f"tex_{tex}", html, f"Texture: {tex}"))

    # --- Texture opacity series ---
    for opacity in [0.05, 0.15, 0.30, 0.50]:
        html = _build_preset_card_html(
            SAMPLE_TEXT, BASE_SLOT_INFO,
            texture_type="grain_film",
            texture_opacity=opacity,
        )
        renders.append((f"tex_opacity_{opacity}", html, f"Texture opacity: {opacity}"))

    # --- Texture blend mode series ---
    for blend in ["normal", "multiply", "overlay"]:
        html = _build_preset_card_html(
            SAMPLE_TEXT, BASE_SLOT_INFO,
            texture_type="grain_film",
            texture_blend_mode=blend,
        )
        renders.append((f"tex_blend_{blend}", html, f"Texture blend: {blend}"))

    # --- Slot types ---
    for slot_type, sample_text in SLOT_SAMPLE_TEXTS.items():
        slot_info = {**BASE_SLOT_INFO, "type": slot_type}
        html = _build_preset_card_html(sample_text, slot_info)
        renders.append((f"slot_{slot_type}", html, f"Slot type: {slot_type}"))

    # --- Recipes ---
    recipes = [
        {
            "name": "cinematic",
            "label": "Cinematic",
            "desc": "Dark bg + diagonal gradient + vignette_heavy",
            "background_color": "#1A1A2E",
            "gradient_direction": "diagonal_tl_br",
            "gradient_colors": ["#1A1A2E", "#16213E", "#0F3460"],
            "texture_type": "vignette_heavy",
            "texture_opacity": 0.6,
        },
        {
            "name": "editorial",
            "label": "Editorial",
            "desc": "Warm preset + paper_subtle texture",
            "preset": "warm",
            "texture_type": "paper_subtle",
            "texture_opacity": 0.25,
        },
        {
            "name": "ambient",
            "label": "Ambient Loop",
            "desc": "Cool preset + radial gradient + flow animation",
            "preset": "cool",
            "gradient_direction": "radial_center",
            "gradient_colors": ["#27AE60", "#1A7A4A", "#0D3B25"],
        },
        {
            "name": "high_contrast",
            "label": "High Contrast",
            "desc": "Red preset + grain_film + pulse animation",
            "preset": "red",
            "texture_type": "grain_film",
            "texture_opacity": 0.20,
        },
    ]
    for recipe in recipes:
        html = _build_preset_card_html(
            SAMPLE_TEXT, BASE_SLOT_INFO,
            preset_name=recipe.get("preset", "default"),
            background_color=recipe.get("background_color"),
            gradient_direction=recipe.get("gradient_direction"),
            gradient_colors=recipe.get("gradient_colors"),
            texture_type=recipe.get("texture_type"),
            texture_opacity=recipe.get("texture_opacity"),
        )
        renders.append((f"recipe_{recipe['name']}", html, f"Recipe: {recipe['label']} — {recipe['desc']}"))

    # --- Render all via Playwright ---
    _log(f"Rendering {len(renders)} static images via Playwright...")
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            for idx, (name, html_content, description) in enumerate(renders):
                out_path = STATIC_DIR / f"{name}.png"
                page = await browser.new_page(viewport={"width": 1080, "height": 1080})
                try:
                    await page.set_content(html_content)
                    await page.screenshot(path=str(out_path), full_page=False)
                finally:
                    await page.close()
                if (idx + 1) % 10 == 0 or idx == len(renders) - 1:
                    _log(f"  Rendered {idx + 1}/{len(renders)} static images")
                progress[name] = description
        finally:
            await browser.close()


async def generate_video_variants(progress: dict) -> None:
    _log("Generating video variants...")

    if not VIDEO_DIR.exists():
        VIDEO_DIR.mkdir(parents=True)

    base_bg = COLORFUL_PRESETS["default"]["background"]
    companion = companion_color(base_bg)
    gradient_colors = [base_bg, companion]

    combos: list[tuple[str, float, float]] = []
    for anim in ALL_ANIM_TYPES:
        for intensity in [0.1, 0.2, 0.4]:
            for speed in [0.5, 1.0]:
                name = f"{anim}_i{intensity}_s{speed}"
                combos.append((name, anim, intensity, speed))

    total_frames = VIDEO_DURATION * VIDEO_FPS

    for idx, (name, anim, intensity, speed) in enumerate(combos):
        out_path = VIDEO_DIR / f"{name}.mp4"
        _log(f"  Video {idx + 1}/{len(combos)}: {name}")

        gen = AnimationFrameGenerator(
            anim_type=anim,
            intensity=intensity,
            speed=speed,
            width=THUMB_SIZE,
            height=THUMB_SIZE,
            seed=42,
            gradient_colors=gradient_colors,
        )

        with VideoEncoder(str(out_path), THUMB_SIZE, THUMB_SIZE, fps=VIDEO_FPS) as enc:
            for frame_idx in range(total_frames):
                t = frame_idx / VIDEO_FPS
                frame = gen.generate_background_frame(t)
                enc.write_frame(frame)

        progress[name] = f"Video: {anim} intensity={intensity} speed={speed}"

    _log(f"Generated {len(combos)} video clips")


async def generate_audio_samples(progress: dict) -> None:
    _log("Generating audio samples...")

    if not AUDIO_DIR.exists():
        AUDIO_DIR.mkdir(parents=True)

    # --- TTS sample ---
    _log("  Generating TTS sample...")
    try:
        from src.renderer.tts import generate_tts

        tts_path = str(AUDIO_DIR / "tts_sample.mp3")
        await generate_tts(SAMPLE_TEXT, tts_path, voice=DEFAULT_TTS_VOICE)
        progress["tts_sample"] = "TTS: en-US-AriaNeural reading sample text"
        _log("  TTS sample generated")
    except Exception as e:
        _log(f"  TTS generation skipped: {e}")
        progress["tts_sample"] = f"TTS: skipped ({e})"

    # --- Background music sample ---
    _log("  Generating background music sample (this may take a few minutes)...")
    try:
        from src.renderer.music_gen import generate_background_music, generate_music_prompt_from_theme

        theme = "The only three things that matter are faith, hope, and love."
        music_prompt = await generate_music_prompt_from_theme(theme)
        _log(f"  Music prompt: {music_prompt}")

        music_duration = 15.0
        music_path = str(AUDIO_DIR / "bg_music_sample.wav")
        await generate_background_music(
            prompt=music_prompt,
            duration=music_duration,
            output_path=music_path,
            steps=ACE_STEP_DEFAULT_STEPS,
            guidance=ACE_STEP_DEFAULT_GUIDANCE,
        )
        progress["bg_music_sample"] = f"BG Music: prompt='{music_prompt}'"
        _log("  Background music sample generated")

        # --- Mixed audio sample ---
        if "tts_sample" in progress and not progress["tts_sample"].startswith("TTS: skipped"):
            _log("  Generating mixed audio sample...")
            from src.renderer.tts import get_audio_duration
            from src.renderer.audio_mix import prepare_slot_audio
            from src.renderer.music_gen import calculate_slot_video_duration

            tts_duration = get_audio_duration(str(AUDIO_DIR / "tts_sample.mp3"))
            slot_duration = calculate_slot_video_duration(tts_duration)

            mixed_path = str(AUDIO_DIR / "mixed_sample.mp3")
            prepare_slot_audio(
                tts_path=str(AUDIO_DIR / "tts_sample.mp3"),
                music_path=music_path,
                output_path=mixed_path,
                tts_duration=tts_duration,
                slot_video_duration=slot_duration,
            )
            progress["mixed_sample"] = "Mixed: TTS + background music"
            _log("  Mixed audio sample generated")
    except Exception as e:
        _log(f"  Music generation skipped: {e}")
        progress["bg_music_sample"] = f"BG Music: skipped ({e})"


def _cli_command(label: str, **overrides) -> str:
    parts = ['acp run-all --theme "..." --year 2026 --month 5']
    for k, v in overrides.items():
        if v is None:
            continue
        if isinstance(v, list):
            parts.append(f'--{k.replace("_", "-")} "{",".join(v)}"')
        elif isinstance(v, float):
            parts.append(f"--{k.replace('_', '-')} {v}")
        elif isinstance(v, bool) and v:
            parts.append(f"--{k.replace('_', '-')}")
        elif isinstance(v, str):
            parts.append(f"--{k.replace('_', '-')} {v}")
    return " \\\n  ".join(parts)


def build_html_gallery(static_variants: dict, video_variants: dict, audio_variants: dict) -> None:
    _log("Building HTML gallery...")

    def _img_card(name: str, description: str, cli: str, width: str = "280px") -> str:
        img_src = f"tutorial_assets/static/{name}.png"
        return f"""
        <div class="variant-card">
            <div class="variant-preview">
                <img src="{img_src}" alt="{description}" loading="lazy">
            </div>
            <div class="variant-label">{description}</div>
            <div class="variant-cli"><code>{cli}</code></div>
        </div>"""

    def _video_card(name: str, description: str, cli: str) -> str:
        video_src = f"tutorial_assets/video/{name}.mp4"
        return f"""
        <div class="variant-card video-card">
            <div class="variant-preview">
                <video src="{video_src}" autoplay loop muted playsinline></video>
            </div>
            <div class="variant-label">{description}</div>
            <div class="variant-cli"><code>{cli}</code></div>
        </div>"""

    def _audio_card(name: str, description: str, label: str) -> str:
        ext = "mp3" if "tts" in name or "mixed" in name else "wav"
        audio_src = f"tutorial_assets/audio/{name}.{ext}"
        return f"""
        <div class="variant-card audio-card">
            <div class="variant-preview audio-preview">
                <div class="audio-icon">&#9835;</div>
                <div class="audio-label">{label}</div>
            </div>
            <div class="variant-label">{description}</div>
            <audio controls src="{audio_src}" preload="auto"></audio>
        </div>"""

    def _section(id: str, title: str, number: str, body: str) -> str:
        return f"""
        <section id="{id}" class="section">
            <div class="section-header">
                <span class="section-num">{number}</span>
                <h2>{title}</h2>
            </div>
            <div class="section-body">
                {body}
            </div>
        </section>"""

    # ---- BUILD SECTIONS ----
    sections = ""

    # 1. Base Post
    cards = _img_card("base_default", "Default blue background, white text, no options",
                      'acp run-all --theme "faith, hope, and love" --year 2026 --month 5')
    sections += _section("base", "The Base Post", "01", cards)

    # 2. Style Presets
    preset_cards = ""
    for name in COLORFUL_PRESETS:
        bg = COLORFUL_PRESETS[name]["background"]
        cli = f'acp run-all --theme "..." --year 2026 --month 5 --background-color {bg}'
        preset_cards += _img_card(f"preset_{name}", f"Preset: {name} ({bg})", cli)

    preset_cards += '<h3 class="sub-heading">Custom Background Colors</h3>'
    custom_colors = [
        ("#1A1A2E", "Dark Navy"),
        ("#F5E6CC", "Warm Cream"),
        ("#2D2D2D", "Charcoal"),
        ("#E8D5B7", "Parchment"),
    ]
    for color, label in custom_colors:
        cli = f'acp run-all --theme "..." --year 2026 --month 5 --background-color {color}'
        preset_cards += _img_card(f"bg_{color.lstrip('#')}", f"{label} ({color})", cli)

    preset_cards += """<div class="info-box">
        <strong>Auto-contrast text:</strong> When <code>--text-color</code> is not set, the pipeline uses
        the WCAG luminance formula to pick black or white text. Light backgrounds (cream, parchment) get
        dark text automatically; dark backgrounds (navy, charcoal) get white text.
    </div>"""

    sections += _section("presets", "Style Presets & Background Colors", "02", preset_cards)

    # 3. Gradients
    grad_cards = ""
    base_bg = COLORFUL_PRESETS["default"]["background"]
    companion = companion_color(base_bg)
    for direction in ALL_GRADIENT_DIRECTIONS:
        cli = f'acp run-all --theme "..." --year 2026 --month 5 \\<br>  --gradient-direction {direction} --gradient-colors "{base_bg},{companion}"'
        grad_cards += _img_card(
            f"grad_{direction}",
            f"Direction: {direction.replace('_', ' ')}",
            cli,
        )

    grad_cards += '<h3 class="sub-heading">Multi-color Gradients</h3>'
    grad_cards += _img_card("grad_3color", "3 colors (40° hue steps)",
                            f'acp run-all ... --gradient-direction diagonal_tl_br --gradient-colors "{base_bg},{companion_color(base_bg, 80)},{companion_color(base_bg, 160)}"')
    grad_cards += _img_card("grad_4color", "4 colors with custom stops [0.0, 0.3, 0.7, 1.0]",
                            'acp run-all ... --gradient-direction diagonal_tl_br --gradient-colors "#FF6B6B,#4ECDC4,#45B7D1,#96CEB4" --gradient-stops "0.0,0.3,0.7,1.0"')

    grad_cards += f"""<div class="info-box">
        <strong>Companion color:</strong> When <code>--gradient-colors</code> is not set, the pipeline
        auto-generates a companion by rotating the background hue 40°. For the default blue ({base_bg}),
        that produces {companion}. Use <code>--gradient-stops</code> to control where each color sits
        (0.0–1.0). Without stops, they're evenly distributed.
    </div>"""

    sections += _section("gradients", "Gradient Directions & Colors", "03", grad_cards)

    # 4. Textures
    tex_cards = ""
    for tex in ALL_TEXTURE_TYPES:
        label = tex.replace("_", " ").title()
        cli = f'acp run-all --theme "..." --year 2026 --month 5 --texture-type {tex}'
        tex_cards += _img_card(f"tex_{tex}", f"Texture: {label}", cli)

    tex_cards += '<h3 class="sub-heading">Opacity Variations (grain_film)</h3>'
    for opacity in [0.05, 0.15, 0.30, 0.50]:
        cli = f'acp run-all ... --texture-type grain_film --texture-opacity {opacity}'
        tex_cards += _img_card(f"tex_opacity_{opacity}", f"Opacity: {opacity}", cli)

    tex_cards += '<h3 class="sub-heading">Blend Mode Variations (grain_film)</h3>'
    for blend in ["normal", "multiply", "overlay"]:
        cli = f'acp run-all ... --texture-type grain_film --texture-blend-mode {blend}'
        tex_cards += _img_card(f"tex_blend_{blend}", f"Blend: {blend}", cli)

    tex_cards += """<div class="info-box">
        <strong>Default texture settings:</strong> <code>--texture-opacity 0.15</code>,
        <code>--texture-blend-mode multiply</code>. Textures are rendered as SVG/CSS overlays at
        <code>z-index: 1</code> — above the background but below the text card at <code>z-index: 2</code>.
    </div>"""

    sections += _section("textures", "Texture Overlays", "04", tex_cards)

    # 5. Animation
    anim_cards = ""
    for anim in ALL_ANIM_TYPES:
        label = anim.title()
        descriptions = {
            "drift": "Smooth diagonal pan — the entire gradient slides diagonally across the viewport",
            "flow": "Organic fluid warping — noise-driven ripples create liquid-like movement",
            "pulse": "Rhythmic brightness breathing — the gradient fades in and out on a sine wave",
            "distortion": "Multi-scale turbulent warping — three octaves of noise displacement",
            "parallax": "Multi-layer depth scroll — three gradient copies move at different speeds (0.3x, 0.6x, 1.0x)",
        }
        desc = descriptions.get(anim, "")

        anim_cards += f'<h3 class="sub-heading">{label}: {desc}</h3>'
        for intensity in [0.1, 0.2, 0.4]:
            for speed in [0.5, 1.0]:
                name = f"{anim}_i{intensity}_s{speed}"
                cli = f'acp run-all ... --animate --anim-type {anim} --anim-intensity {intensity} --anim-speed {speed} --anim-loop 60'
                anim_cards += _video_card(
                    name,
                    f"{label} — intensity={intensity}, speed={speed}",
                    cli,
                )

    anim_cards += """<div class="info-box">
        <strong>Animation parameters:</strong> <code>--anim-intensity</code> (0.0–0.5, default 0.2)
        controls how much movement. <code>--anim-speed</code> (0.1–2.0, default 1.0) controls rate.
        <code>--anim-loop</code> (seconds, default 60) sets clip duration. <code>--anim-seed</code>
        makes animations deterministic for reproducibility.<br><br>
        <strong>Important:</strong> Using <code>--animate</code> automatically enables
        <code>--audio</code> and <code>--bg-music</code>. The pipeline generates TTS narration
        and background music for each post, then mixes them together.
    </div>"""

    sections += _section("animation", "Animation Types", "05", anim_cards)

    # 6. Audio
    audio_cards = ""

    audio_cards += '<h3 class="sub-heading">Text-to-Speech (TTS)</h3>'
    audio_cards += """<div class="info-box">
        Powered by <strong>edge-tts</strong> (Microsoft Edge TTS). The <code>--audio</code> flag
        generates an MP3 narration of the post text. Choose a voice with
        <code>--audio-voice</code> (default: <code>en-US-AriaNeural</code>). Other options:
        <code>en-US-GuyNeural</code>, <code>en-US-JennyNeural</code>, <code>en-GB-SoniaNeural</code>.
    </div>"""
    if "tts_sample" in audio_variants:
        audio_cards += _audio_card("tts_sample", audio_variants["tts_sample"], "TTS Narration")

    audio_cards += '<h3 class="sub-heading">Background Music</h3>'
    audio_cards += """<div class="info-box">
        Powered by <strong>ACE-Step</strong> AI music generation. The <code>--bg-music</code> flag
        generates instrumental background music. Use <code>--bg-music-prompt</code> to describe the
        mood, instruments, tempo, and atmosphere. If not provided, the pipeline auto-generates a prompt
        from the monthly theme via Ollama. Music is generated for the full month and reused per post.
    </div>"""
    if "bg_music_sample" in audio_variants and not audio_variants["bg_music_sample"].startswith("BG Music: skipped"):
        audio_cards += _audio_card("bg_music_sample", audio_variants["bg_music_sample"], "Background Music")

    audio_cards += '<h3 class="sub-heading">Mixed Audio (TTS + Music)</h3>'
    audio_cards += f"""<div class="info-box">
        The final audio mix places TTS at volume 1.0 with a {ACE_STEP_TTS_DELAY}s delay, then layers
        background music at volume {ACE_STEP_MUSIC_VOLUME}. Output is mono 44100Hz. The music track
        is trimmed to the slot video duration (TTS duration + {ACE_STEP_TAIL_RATIO:.0%} tail, max {ACE_STEP_TAIL_MAX}s).
    </div>"""
    if "mixed_sample" in audio_variants:
        audio_cards += _audio_card("mixed_sample", audio_variants["mixed_sample"], "Mixed: TTS + Music")

    sections += _section("audio", "Audio: TTS & Background Music", "06", audio_cards)

    # 7. Post Types
    slot_cards = ""
    for slot_type, sample_text in SLOT_SAMPLE_TEXTS.items():
        label = slot_type.replace("_", " ").title()
        max_words = SLOT_MAX_WORDS.get(slot_type, "?")
        color = SLOT_COLORS.get(slot_type, "#6B7280")
        cli = f"(AI assigns this slot type via monthly planner — max {max_words} words)"
        card_html = _img_card(f"slot_{slot_type}", f"{label} (max {max_words} words)", cli)
        slot_cards += card_html

    slot_cards += """<div class="info-box">
        <strong>Slot assignment:</strong> The AI planner assigns one of these 6 types to each
        Mon–Sat of the month. Each type can appear 0–2 times per week. Sundays are always
        <code>human_intentional</code> — reserved for your own writing. The planner avoids
        repeating the same type on consecutive days.<br><br>
        <strong>Post-generation tools:</strong>
        <ul>
            <li><code>acp preview</code> — HTML preview of all generated text for the month</li>
            <li><code>acp regen-text --dates 2026-05-04,2026-05-05</code> — regenerate specific dates</li>
            <li><code>acp rerender --date 2026-05-04 --texture-type grain_film</code> — re-render with new visual settings</li>
            <li><code>acp refine-posts --feedback "2026-05-04::Make it more direct"</code> — AI-assisted iterative refinement</li>
        </ul>
    </div>"""

    sections += _section("post-types", "Post Types (Slot Functions)", "07", slot_cards)

    # 8. Recipes
    recipe_cards = ""
    recipe_configs = [
        {
            "name": "cinematic",
            "label": "Cinematic",
            "cli": 'acp run-all --theme "..." --year 2026 --month 5 \\\n  --background-color "#1A1A2E" \\\n  --gradient-direction diagonal_tl_br --gradient-colors "#1A1A2E,#16213E,#0F3460" \\\n  --texture-type vignette_heavy --texture-opacity 0.6 \\\n  --animate --anim-type drift --anim-intensity 0.2',
        },
        {
            "name": "editorial",
            "label": "Editorial",
            "cli": 'acp run-all --theme "..." --year 2026 --month 5 \\\n  --background-color "#E67E22" \\\n  --texture-type paper_subtle --texture-opacity 0.25',
        },
        {
            "name": "ambient",
            "label": "Ambient Loop",
            "cli": 'acp run-all --theme "..." --year 2026 --month 5 \\\n  --background-color "#27AE60" \\\n  --gradient-direction radial_center --gradient-colors "#27AE60,#1A7A4A,#0D3B25" \\\n  --animate --anim-type flow --anim-intensity 0.2 --anim-speed 0.5',
        },
        {
            "name": "high_contrast",
            "label": "High Contrast",
            "cli": 'acp run-all --theme "..." --year 2026 --month 5 \\\n  --background-color "#C0392B" \\\n  --texture-type grain_film --texture-opacity 0.20 \\\n  --animate --anim-type pulse --anim-intensity 0.3',
        },
    ]
    for recipe in recipe_configs:
        recipe_cards += _img_card(
            f"recipe_{recipe['name']}",
            recipe["label"],
            recipe["cli"],
        )

    sections += _section("recipes", "Recipes: Combined Variants", "08", recipe_cards)

    # ---- COMPOSE FULL HTML ----
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ACP Tutorial Explorer</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
        background: #0A0A0A;
        color: #E0E0E0;
        line-height: 1.6;
    }}

    .top-bar {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 56px;
        background: #111111;
        border-bottom: 1px solid #222222;
        display: flex;
        align-items: center;
        padding: 0 24px;
        z-index: 100;
    }}

    .top-bar h1 {{
        font-size: 16px;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.3px;
    }}

    .top-bar .subtitle {{
        font-size: 12px;
        color: #666666;
        margin-left: 12px;
    }}

    .sidebar {{
        position: fixed;
        top: 56px;
        left: 0;
        width: 240px;
        height: calc(100vh - 56px);
        background: #0E0E0E;
        border-right: 1px solid #1A1A1A;
        overflow-y: auto;
        padding: 20px 0;
        z-index: 90;
    }}

    .sidebar a {{
        display: block;
        padding: 10px 20px;
        color: #888888;
        text-decoration: none;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.15s ease;
        border-left: 2px solid transparent;
    }}

    .sidebar a:hover {{
        color: #CCCCCC;
        background: #161616;
        border-left-color: #444444;
    }}

    .sidebar a.active {{
        color: #FFFFFF;
        background: #1A1A1A;
        border-left-color: #4A90E2;
    }}

    .main {{
        margin-left: 240px;
        margin-top: 56px;
        padding: 40px 48px 80px;
        max-width: 1400px;
    }}

    .section {{
        margin-bottom: 80px;
        scroll-margin-top: 72px;
    }}

    .section-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid #1E1E1E;
    }}

    .section-num {{
        background: #4A90E2;
        color: #FFFFFF;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }}

    .section-header h2 {{
        font-size: 22px;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.3px;
    }}

    .sub-heading {{
        font-size: 15px;
        font-weight: 600;
        color: #AAAAAA;
        margin: 32px 0 16px;
        padding-top: 16px;
        border-top: 1px solid #1A1A1A;
    }}

    .variant-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
    }}

    .variant-card {{
        background: #141414;
        border: 1px solid #222222;
        border-radius: 8px;
        overflow: hidden;
        width: 280px;
        flex-shrink: 0;
    }}

    .variant-card video-card {{
        width: 300px;
    }}

    .variant-preview {{
        width: 280px;
        height: 280px;
        overflow: hidden;
        background: #0A0A0A;
    }}

    .variant-preview img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}

    .variant-preview video {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}

    .variant-label {{
        padding: 10px 14px;
        font-size: 13px;
        font-weight: 600;
        color: #CCCCCC;
    }}

    .variant-cli {{
        padding: 0 14px 10px;
    }}

    .variant-cli code {{
        font-family: "SF Mono", "Fira Code", "Cascadia Code", monospace;
        font-size: 11px;
        color: #888888;
        background: #0A0A0A;
        padding: 6px 10px;
        border-radius: 4px;
        display: block;
        white-space: pre-wrap;
        word-break: break-all;
        line-height: 1.5;
    }}

    .info-box {{
        background: #141414;
        border: 1px solid #1E1E1E;
        border-left: 3px solid #4A90E2;
        border-radius: 6px;
        padding: 16px 20px;
        margin-top: 24px;
        font-size: 14px;
        color: #BBBBBB;
        line-height: 1.7;
    }}

    .info-box strong {{
        color: #FFFFFF;
    }}

    .info-box code {{
        background: #1A1A1A;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 12px;
        color: #7EB8F0;
    }}

    .info-box ul {{
        margin: 8px 0 0 20px;
    }}

    .info-box li {{
        margin-bottom: 4px;
    }}

    .audio-card {{
        width: 320px;
    }}

    .audio-preview {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        height: 120px;
    }}

    .audio-icon {{
        font-size: 48px;
        color: #4A90E2;
    }}

    .audio-label {{
        font-size: 16px;
        font-weight: 600;
        color: #CCCCCC;
    }}

    .audio-card audio {{
        width: 100%;
        padding: 0 14px 14px;
    }}

    @media (max-width: 1100px) {{
        .sidebar {{ display: none; }}
        .main {{ margin-left: 0; padding: 40px 24px 80px; }}
    }}
</style>
</head>
<body>

<div class="top-bar">
    <h1>ACP Variants Explorer</h1>
    <span class="subtitle">Interactive tutorial for the Ambient Content Pipeline</span>
</div>

<nav class="sidebar" id="sidebar">
    <a href="#base">01 — The Base Post</a>
    <a href="#presets">02 — Style Presets</a>
    <a href="#gradients">03 — Gradients</a>
    <a href="#textures">04 — Textures</a>
    <a href="#animation">05 — Animation</a>
    <a href="#audio">06 — Audio</a>
    <a href="#post-types">07 — Post Types</a>
    <a href="#recipes">08 — Recipes</a>
</nav>

<div class="main">
    {sections}
</div>

<script>
(function() {{
    const links = document.querySelectorAll('.sidebar a');
    const sections = document.querySelectorAll('.section');

    const observer = new IntersectionObserver((entries) => {{
        entries.forEach(entry => {{
            if (entry.isIntersecting) {{
                links.forEach(l => l.classList.remove('active'));
                const link = document.querySelector(`.sidebar a[href="#${{entry.target.id}}"]`);
                if (link) link.classList.add('active');
            }}
        }});
    }}, {{ rootMargin: '-80px 0px -70% 0px' }});

    sections.forEach(s => observer.observe(s));
}})();
</script>

</body>
</html>"""

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    _log(f"Gallery written to {OUTPUT_HTML}")


async def main() -> None:
    print("=" * 60)
    print("  ACP Tutorial Explorer Generator")
    print("=" * 60)
    print()

    static_variants: dict[str, str] = {}
    video_variants: dict[str, str] = {}
    audio_variants: dict[str, str] = {}

    # Phase 1: Setup
    _log("Setting up directories...")
    for d in [STATIC_DIR, VIDEO_DIR, AUDIO_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Phase 2: Static images
    t0 = time.time()
    await generate_static_variants(static_variants)
    _log(f"Static images done in {time.time() - t0:.1f}s")

    # Phase 3: Videos
    t0 = time.time()
    await generate_video_variants(video_variants)
    _log(f"Videos done in {time.time() - t0:.1f}s")

    # Phase 4: Audio
    t0 = time.time()
    await generate_audio_samples(audio_variants)
    _log(f"Audio done in {time.time() - t0:.1f}s")

    # Phase 5: Build HTML
    build_html_gallery(static_variants, video_variants, audio_variants)

    print()
    print("=" * 60)
    print(f"  Done! Open {OUTPUT_HTML} in your browser.")
    print(f"  Static images: {len(static_variants)}")
    print(f"  Video clips:   {len(video_variants)}")
    print(f"  Audio samples: {len(audio_variants)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
