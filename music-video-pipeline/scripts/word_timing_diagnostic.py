#!/usr/bin/env python3
"""Word-timing waveform diagnostic for lyric-video sync auditing.

For each lyric line, renders the audio waveform region around the line's
claimed word timestamps so a human can judge whether the marked boundaries
land on the actual vocal onsets.

Usage:
  python3 scripts/word_timing_diagnostic.py --project <project_dir> \
      [--lines 0,1,2] [--context 0.3] [--out DIR]

Outputs <out>/line-<idx>.png + index.html. Dependencies: PIL, numpy, ffmpeg.
Read-only with respect to all project data.
"""
from __future__ import annotations

import argparse
import html
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SR = 8000  # decode sample rate for envelope (plenty for timing review)
WIDTH = 1500
HEIGHT = 380
MARGIN_L, MARGIN_R = 70, 20
MARGIN_T, MARGIN_B = 46, 60

COLOR_BG = (16, 16, 28)
COLOR_WAVE = (120, 200, 240)
COLOR_WAVE_PEAK = (190, 230, 255)
COLOR_ZERO = (60, 60, 80)
COLOR_WORD_START = (80, 220, 255)
COLOR_WORD_END = (255, 170, 60)
COLOR_ONSET = (80, 255, 120)
COLOR_LINE_SPAN = (255, 90, 90)
COLOR_TEXT = (230, 230, 230)
COLOR_DIM = (140, 140, 150)


def _font(size: int):
    for cand in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ):
        try:
            return ImageFont.truetype(cand, size)
        except Exception:
            continue
    return ImageFont.load_default()


def decode_window(audio: Path, t_start: float, duration: float, sr: int = SR) -> np.ndarray:
    """Decode [t_start, t_start+duration) to mono float array via ffmpeg."""
    proc = subprocess.run(
        [
            "ffmpeg", "-v", "error",
            "-ss", f"{t_start:.3f}", "-t", f"{duration:.3f}",
            "-i", str(audio),
            "-ac", "1", "-ar", str(sr),
            "-f", "s16le", "pipe:1",
        ],
        capture_output=True, check=True,
    )
    return np.frombuffer(proc.stdout, np.int16).astype(np.float32) / 32768.0


def load_onsets(path: Path) -> list[float]:
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [float(x) for x in data.get("onset_times", [])]


def render_line_image(
    line: dict,
    line_idx: int,
    section: str,
    audio: Path,
    onsets: list[float],
    out_path: Path,
    context: float,
) -> dict:
    words = [w for w in line.get("words", []) if w.get("start") is not None]
    w_first, w_last = words[0]["start"], words[-1]["end"]
    win_a = min(line.get("start", w_first), w_first) - context
    win_b = max(line.get("end", w_last), w_last) + context
    duration = win_b - win_a

    samples = decode_window(audio, win_a, duration)
    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)
    f_small = _font(13)
    f_label = _font(16)
    f_title = _font(20)

    plot_l, plot_r = MARGIN_L, WIDTH - MARGIN_R
    plot_t, plot_b = MARGIN_T, HEIGHT - MARGIN_B
    plot_w, plot_h = plot_r - plot_l, plot_b - plot_t
    zero_y = plot_t + plot_h // 2

    def t_to_x(t: float) -> float:
        return plot_l + (t - win_a) / duration * plot_w

    # claimed line span shading (shows where the LINE claims to be active)
    ls, le = line.get("start"), line.get("end")
    if ls is not None and le is not None:
        x0, x1 = t_to_x(max(ls, win_a)), t_to_x(min(le, win_b))
        draw.rectangle([x0, plot_t, x1, plot_b], fill=(28, 28, 46))

    # waveform envelope (per-column min/max)
    n = len(samples)
    if n:
        col_span = n / plot_w
        for px in range(plot_l, plot_r):
            a = int((px - plot_l) * col_span)
            b = max(a + 1, int((px - plot_l + 1) * col_span))
            chunk = samples[a:b]
            lo, hi = float(chunk.min()), float(chunk.max())
            y0 = zero_y - hi * (plot_h / 2 - 4)
            y1 = zero_y - lo * (plot_h / 2 - 4)
            draw.line([(px, y0), (px, y1)], fill=COLOR_WAVE)
    draw.line([(plot_l, zero_y), (plot_r, zero_y)], fill=COLOR_ZERO)

    # vocal onsets (green ticks along the bottom)
    for on in onsets:
        if win_a <= on <= win_b:
            x = t_to_x(on)
            draw.line([(x, plot_b - 14), (x, plot_b - 2)], fill=COLOR_ONSET, width=2)

    # word boundaries + labels
    for w in words:
        x_s, x_e = t_to_x(w["start"]), t_to_x(w["end"])
        src = w.get("source", "")
        start_col = COLOR_WORD_START if "onset" in src else (200, 130, 255)
        draw.line([(x_s, plot_t), (x_s, plot_b)], fill=start_col, width=2)
        draw.line([(x_e, plot_t), (x_e, plot_b)], fill=COLOR_WORD_END, width=1)
        draw.text((x_s + 2, plot_t + 2), w["text"], fill=COLOR_TEXT, font=f_small)
        # nearest onset delta annotation
        near = [o for o in onsets if abs(o - w["start"]) <= 0.15]
        if near:
            delta = min(near, key=lambda o: abs(o - w["start"])) - w["start"]
            draw.text((x_s + 2, plot_t + 18), f"Δ{delta:+.2f}s",
                      fill=COLOR_ONSET if abs(delta) < 0.06 else (255, 120, 120),
                      font=f_small)

    # claimed line start/end markers
    if ls is not None:
        draw.line([(t_to_x(ls), plot_b - 18), (t_to_x(ls), plot_b - 2)],
                  fill=COLOR_LINE_SPAN, width=2)
    if le is not None:
        draw.line([(t_to_x(le), plot_b - 18), (t_to_x(le), plot_b - 2)],
                  fill=COLOR_LINE_SPAN, width=2)

    # time axis
    step = 0.1 if duration < 4 else (0.25 if duration < 8 else 0.5)
    t = win_a
    while t <= win_b:
        x = t_to_x(t)
        draw.line([(x, plot_b), (x, plot_b + 5)], fill=COLOR_DIM)
        draw.text((x - 14, plot_b + 8), f"{t:.2f}", fill=COLOR_DIM, font=f_small)
        t += step

    # header
    draw.text((MARGIN_L, 8),
              f"L{line_idx} [{section}]  \"{line.get('text', '').strip()}\"",
              fill=COLOR_TEXT, font=f_title)
    draw.text((MARGIN_L, 30 - 6),
              f"line {ls:.2f}–{le:.2f}s  |  words {w_first:.2f}–{w_last:.2f}s  |  "
              f"window {win_a:.2f}–{win_b:.2f}s  |  "
              f"cyan=word start (purple=whisper-only), orange=word end, green tick=vocal onset, red=line span",
              fill=COLOR_DIM, font=f_small)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return {
        "line_idx": line_idx,
        "text": line.get("text", "").strip(),
        "window": [round(win_a, 3), round(win_b, 3)],
        "words": [
            {"text": w["text"], "start": w["start"], "end": w["end"],
             "source": w.get("source", "")}
            for w in words
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True, help="project dir containing data/")
    ap.add_argument("--lines", help="comma-separated line indices (default: all)")
    ap.add_argument("--context", type=float, default=0.3, help="seconds of context each side")
    ap.add_argument("--out", help="output dir (default: <project>/output/timing-diag)")
    args = ap.parse_args()

    project = Path(args.project)
    data = project / "data"
    out = Path(args.out) if args.out else project / "output" / "timing-diag"
    out.mkdir(parents=True, exist_ok=True)

    synced = json.loads((data / "lyrics_synced.json").read_text())
    lines = synced["lines"]
    onsets = load_onsets(data / "vocal_onsets.json")
    audio = data / "HERE GOES.wav"
    if not audio.exists():
        cand = sorted(data.glob("*.wav"))
        audio = cand[0] if cand else None
    if audio is None:
        raise SystemExit("no .wav audio found in data/")

    wanted = None
    if args.lines:
        wanted = {int(x) for x in args.lines.split(",")}

    section = ""
    index_rows = []
    for li, line in enumerate(lines):
        if wanted is not None and li not in wanted:
            continue
        sec = (line.get("section") or {}).get("raw_marker", "")
        if sec:
            section = sec
        info = render_line_image(
            line, li, section, audio, onsets,
            out / f"line-{li:03d}.png", args.context,
        )
        index_rows.append(info)

    rows_html = []
    for info in index_rows:
        w = info["words"]
        wtxt = html.escape(" ".join(x["text"] for x in w))
        rows_html.append(
            f'<li><a href="line-{info["line_idx"]:03d}.png">L{info["line_idx"]}</a> '
            f'— {wtxt} <span style="color:#888">({info["window"][0]:.2f}–{info["window"][1]:.2f}s)</span></li>'
        )
    (out / "index.html").write_text(
        "<!doctype html><meta charset=utf-8><title>word-timing waveform audit</title>"
        "<body style='background:#111;color:#ddd;font-family:monospace'>"
        "<h2>Word-timing waveform audit</h2>"
        "<p>cyan = word start (purple = whisper-only source) · orange = word end · "
        "green tick = vocal onset · red = claimed line span. "
        "Δn.ns = nearest onset minus claimed word start.</p>"
        "<ul>" + "".join(rows_html) + "</ul>",
        encoding="utf-8",
    )
    print(f"wrote {len(index_rows)} line images + index.html to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
