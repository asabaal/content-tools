from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .moods import MOODS, MoodProfile, DEFAULT_MOOD
from .palette import generate_palette, generate_line_colors, SectionColor
from .rules import (
    SectionProfile,
    assign_section_visual,
    assign_word_positions,
    compute_emphasis_overrides,
)


@dataclass
class GenerateResult:
    script: dict
    sections_profiled: int
    variance_detected: str
    mood_used: str


class ScriptGenerator:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.data_dir = project_dir / "data" if (project_dir / "data").exists() else project_dir
        self.analysis: dict = {}
        self.lyrics_raw: dict = {}
        self.lyrics_synced: dict = {}
        self.song_name: str = ""
        self._load_data()

    def _load_data(self) -> None:
        for name, target in [
            ("analysis.json", "analysis"),
            ("lyrics_raw.json", "lyrics_raw"),
            ("lyrics_synced.json", "lyrics_synced"),
        ]:
            p = self.data_dir / name
            if p.exists():
                setattr(self, target, json.loads(p.read_text(encoding="utf-8")))

        proj_path = self.data_dir / "mvp_project.json"
        if proj_path.exists():
            proj = json.loads(proj_path.read_text(encoding="utf-8"))
            self.song_name = proj.get("name", "")

    def generate(
        self,
        mood: str | None = None,
        base_color: str | None = None,
        variance: str = "auto",
    ) -> GenerateResult:
        mood_key = mood or DEFAULT_MOOD
        mood_profile = MOODS.get(mood_key, MOODS[DEFAULT_MOOD])

        sections = self._build_sections()
        profiles = self._build_profiles(sections)
        energies = [p.energy for p in profiles]

        variance_float = self._resolve_variance(variance, energies)
        variance_label = (
            "low" if variance_float < 0.4 else "high" if variance_float > 0.7 else "medium"
        )

        colors = generate_palette(
            section_types=[p.section_type for p in profiles],
            energies=energies,
            mood=mood_profile,
            variance=variance_float,
            base_color=base_color,
        )

        script_sections = []
        for i, (profile, color) in enumerate(zip(profiles, colors)):
            visual = assign_section_visual(profile, color, mood_profile, mood_key, variance_float, i)

            line_overrides = {}
            num_lines = profile.end_line - profile.start_line + 1
            line_colors = generate_line_colors(color, num_lines, mood_key, variance_float)

            for li, line_idx in enumerate(range(profile.start_line, profile.end_line + 1)):
                is_title = self._is_title_line(line_idx)
                is_start = line_idx == profile.start_line
                ov = compute_emphasis_overrides(
                    profile, visual, self.song_name, is_title, is_start,
                )
                ov["background_color"] = line_colors[li].primary
                if visual.get("background_type") == "gradient":
                    ov["gradient_colors"] = [line_colors[li].primary, line_colors[li].companion]
                line_overrides[str(line_idx)] = ov

            sec = {
                "name": profile.name,
                "type": profile.section_type,
                "lines": list(range(profile.start_line, profile.end_line + 1)),
                "visual": visual,
                "lines_overrides": line_overrides,
            }

            synced_lines = self.lyrics_synced.get("lines", [])
            word_overrides = assign_word_positions(
                profile, visual.get("text_position", "center"),
                mood_key, variance_float, synced_lines,
            )
            if word_overrides:
                sec["words_overrides"] = word_overrides

            script_sections.append(sec)

        defaults = self._build_defaults(mood_profile, profiles, colors)
        caption_style = self._build_caption_style(mood_profile, variance_float)

        script = {
            "name": self.song_name,
            "defaults": defaults,
            "caption_style": caption_style,
            "sections": script_sections,
        }

        return GenerateResult(
            script=script,
            sections_profiled=len(profiles),
            variance_detected=variance_label,
            mood_used=mood_key,
        )

    def _build_sections(self) -> list[dict]:
        raw_lines = self.lyrics_raw.get("lines", [])
        if not raw_lines:
            return []

        sections = []
        current_marker = None
        current_type = None
        current_name = None
        current_tags: list[str] = []
        start_line = 0

        for line in raw_lines:
            sec = line.get("section", {})
            stype = sec.get("section_type", "verse")
            raw_marker = sec.get("raw_marker", stype)
            tags = sec.get("tags", [])

            if raw_marker != current_marker or current_marker is None:
                if current_marker is not None:
                    sections.append({
                        "type": current_type,
                        "name": current_name or current_type.capitalize(),
                        "tags": current_tags,
                        "start_line": start_line,
                        "end_line": line.get("index", 0) - 1,
                    })
                current_marker = raw_marker
                current_type = stype
                current_name = raw_marker
                current_tags = tags
                start_line = line.get("index", 0)

        if current_marker is not None:
            last_idx = raw_lines[-1].get("index", 0)
            sections.append({
                "type": current_type,
                "name": current_name or current_type.capitalize(),
                "tags": current_tags,
                "start_line": start_line,
                "end_line": last_idx,
            })

        return sections

    def _build_profiles(self, sections: list[dict]) -> list[SectionProfile]:
        synced_lines = self.lyrics_synced.get("lines", [])
        profiles = []

        for sec in sections:
            sl = sec["start_line"]
            el = sec["end_line"]
            sname = sec["name"]
            stype = sec["type"]
            tags = sec.get("tags", [])

            start_time = 0.0
            end_time = 0.0
            word_count = 0

            for idx in range(sl, min(el + 1, len(synced_lines))):
                line = synced_lines[idx]
                if start_time == 0.0 or line.get("start", 0) < start_time:
                    start_time = line.get("start", 0)
                if line.get("end", 0) > end_time:
                    end_time = line.get("end", 0)
                word_count += len(line.get("words", []))

            duration = max(0.1, end_time - start_time)
            pace = word_count / duration if duration > 0 else 2.0

            energy = self._section_energy(start_time, end_time)
            centroid = self._section_centroid(start_time, end_time)

            profiles.append(SectionProfile(
                section_type=stype,
                name=sname,
                start_line=sl,
                end_line=el,
                start_time=start_time,
                end_time=end_time,
                energy=energy,
                spectral_centroid=centroid,
                pace=pace,
                tags=tags,
                word_count=word_count,
            ))

        return profiles

    def _section_energy(self, start: float, end: float) -> float:
        rms = self.analysis.get("rms_energy", [])
        sr = self.analysis.get("sample_rate", 48000)
        if not rms:
            return 0.5
        hop = 512
        fps = sr / hop
        start_idx = int(start * fps)
        end_idx = int(end * fps)
        segment = rms[start_idx:end_idx]
        if not segment:
            return 0.5
        return sum(segment) / len(segment)

    def _section_centroid(self, start: float, end: float) -> float:
        centroids = self.analysis.get("spectral_centroids", [])
        sr = self.analysis.get("sample_rate", 48000)
        if not centroids:
            return 0.5
        hop = 512
        fps = sr / hop
        start_idx = int(start * fps)
        end_idx = int(end * fps)
        segment = centroids[start_idx:end_idx]
        if not segment:
            return 0.5
        return sum(segment) / len(segment)

    def _resolve_variance(self, variance: str, energies: list[float]) -> float:
        if variance in ("low", "medium", "high"):
            return {"low": 0.25, "medium": 0.55, "high": 0.85}[variance]
        if not energies:
            return 0.5
        mean = sum(energies) / len(energies)
        if mean == 0:
            return 0.5
        var = sum((e - mean) ** 2 for e in energies) / len(energies)
        std = var ** 0.5
        ratio = std / mean
        return max(0.15, min(0.9, ratio * 2.5))

    def _is_title_line(self, line_idx: int) -> bool:
        if not self.song_name:
            return False
        synced_lines = self.lyrics_synced.get("lines", [])
        if line_idx >= len(synced_lines):
            return False
        text = synced_lines[line_idx].get("text", "").lower().strip()
        title = self.song_name.lower().strip()
        return title in text

    def _build_defaults(
        self,
        mood: MoodProfile,
        profiles: list[SectionProfile],
        colors: list[SectionColor],
    ) -> dict:
        if colors:
            primary = colors[0].primary
            companion = colors[0].companion
        else:
            primary = "#1a1a2e"
            companion = "#16213e"

        return {
            "background_type": "gradient" if mood.gradient_likely else "solid",
            "background_color": primary,
            "gradient_colors": [primary, companion],
            "gradient_direction": mood.direction,
            "texture_type": mood.texture_default,
            "texture_opacity": 0.2,
            "texture_blend_mode": "multiply",
            "text_auto_contrast": True,
            "font_size": 48,
            "animation_type": "fade",
            "animation_speed": 1.0,
            "reveal_mode": "progressive",
            "reveal_words": 1,
            "reveal_slide": False,
            "reactivity": ["vocals"],
        }

    def _build_caption_style(self, mood: MoodProfile, variance: float) -> dict:
        highlight = "#4cc9f0"
        if mood.base_hue < 60 or mood.base_hue > 300:
            highlight = "#ff6b6b"
        elif 150 < mood.base_hue < 270:
            highlight = "#4cc9f0"
        else:
            highlight = "#f0a04c"
        return {
            "font_family": 0,
            "highlight_color": highlight,
            "text_position": "center",
            "letter_spacing": 1,
            "text_shadow": False,
            "outline": False,
        }


def generate_script(project_dir: Path, **kwargs) -> GenerateResult:
    return ScriptGenerator(project_dir).generate(**kwargs)
