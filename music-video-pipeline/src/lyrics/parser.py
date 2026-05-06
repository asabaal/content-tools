from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

logger = logging.getLogger(__name__)

SECTION_MARKER_RE = re.compile(r"^\[(.+)\]\s*$")


@dataclass
class LyricWord:
    text: str
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start

    def is_active(self, time: float) -> bool:
        return self.start <= time <= self.end

    def to_dict(self) -> dict:
        return {"text": self.text, "start": round(self.start, 3), "end": round(self.end, 3)}


@dataclass
class LyricSection:
    raw_marker: str
    section_type: str
    index: Optional[int] = None
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"raw_marker": self.raw_marker, "section_type": self.section_type, "index": self.index, "tags": self.tags}


@dataclass
class LyricLine:
    index: int
    text: str
    start: float
    end: float
    words: List[LyricWord] = field(default_factory=list)
    section: Optional[LyricSection] = None

    @property
    def duration(self) -> float:
        return self.end - self.start

    def is_active(self, time: float) -> bool:
        return self.start <= time <= self.end

    def get_active_words(self, time: float) -> List[LyricWord]:
        return [w for w in self.words if w.is_active(time)]

    def get_progress(self, time: float) -> float:
        if time < self.start:
            return 0.0
        if time > self.end:
            return 1.0
        return (time - self.start) / self.duration if self.duration > 0 else 0.0

    def to_dict(self) -> dict:
        d = {
            "index": self.index,
            "text": self.text,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "words": [w.to_dict() for w in self.words],
        }
        if self.section:
            d["section"] = self.section.to_dict()
        return d


@dataclass
class LyricsResult:
    format: str
    source_file: str
    lines: List[LyricLine]
    sections: List[LyricSection] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        return len(self.lines)

    @property
    def total_words(self) -> int:
        return sum(len(line.words) for line in self.lines)

    @property
    def first_line_time(self) -> Optional[float]:
        return self.lines[0].start if self.lines else None

    @property
    def last_line_time(self) -> Optional[float]:
        return self.lines[-1].end if self.lines else None

    def to_dict(self) -> dict:
        return {
            "format": self.format,
            "source_file": self.source_file,
            "total_lines": self.total_lines,
            "total_words": self.total_words,
            "has_sections": len(self.sections) > 0,
            "section_count": len(self.sections),
            "lines": [line.to_dict() for line in self.lines],
            "sections": [s.to_dict() for s in self.sections],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def _parse_section_marker(text: str) -> Optional[LyricSection]:
    m = SECTION_MARKER_RE.match(text.strip())
    if not m:
        return None
    raw = m.group(1)
    parts = [p.strip() for p in raw.split(",")]
    section_type = parts[0].strip().lower()
    section_type = re.sub(r"\s+", "_", section_type)
    index = None
    tags = []
    type_match = re.match(r"^(.+?)\s+(\d+)$", parts[0].strip())
    if type_match:
        section_type = type_match.group(1).strip().lower().replace(" ", "_")
        index = int(type_match.group(2))
    for tag_part in parts[1:]:
        tag = tag_part.strip().lower().replace(" ", "_")
        if tag:
            tags.append(tag)
    return LyricSection(raw_marker=raw, section_type=section_type, index=index, tags=tags)


class LyricParser:
    def parse_file(self, file_path: Union[str, Path]) -> LyricsResult:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Lyrics file not found: {file_path}")

        ext = file_path.suffix.lower()
        content = file_path.read_text(encoding="utf-8")

        if ext == ".srt":
            lines = self._parse_srt(content)
            sections = []
        elif ext == ".lrc":
            lines = self._parse_lrc(content)
            sections = []
        elif ext == ".txt":
            lines, sections = self._parse_plain_text(content)
        else:
            raise ValueError(f"Unsupported lyrics format: {ext}. Supported: .srt, .lrc, .txt")

        return LyricsResult(format=ext.lstrip("."), source_file=file_path.name, lines=lines, sections=sections)

    def _parse_srt(self, content: str) -> List[LyricLine]:
        lines: List[LyricLine] = []
        blocks = re.split(r"\n\s*\n", content.strip())
        line_idx = 0

        for block in blocks:
            parts = block.strip().split("\n")
            if len(parts) < 3:
                continue

            timing = re.match(
                r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
                parts[1],
            )
            if not timing:
                continue

            text = " ".join(parts[2:]).strip()
            if text:
                start = self._srt_to_seconds(*[int(timing.group(i)) for i in range(1, 5)])
                end = self._srt_to_seconds(*[int(timing.group(i)) for i in range(5, 9)])
                words = self._make_words(text, start, end)
                lines.append(LyricLine(index=line_idx, text=text, start=start, end=end, words=words))
                line_idx += 1

        return lines

    def _parse_lrc(self, content: str) -> List[LyricLine]:
        lines: List[LyricLine] = []
        lrc_lines = content.strip().split("\n")
        parsed = []

        for i, raw in enumerate(lrc_lines):
            m = re.match(r"\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\]\s*(.*)", raw)
            if not m:
                continue
            minutes = int(m.group(1))
            seconds = int(m.group(2))
            cs = m.group(3)
            fraction = int(cs) / (100 if len(cs) == 2 else 1000) if cs else 0.0
            start = minutes * 60 + seconds + fraction
            text = m.group(4).strip()
            if text:
                parsed.append((start, text))

        line_idx = 0
        for i, (start, text) in enumerate(parsed):
            end = parsed[i + 1][0] if i + 1 < len(parsed) else start + 3.0
            words = self._make_words(text, start, end)
            lines.append(LyricLine(index=line_idx, text=text, start=start, end=end, words=words))
            line_idx += 1

        return lines

    def _parse_plain_text(self, content: str, default_duration: float = 3.0) -> tuple[List[LyricLine], List[LyricSection]]:
        lines: List[LyricLine] = []
        sections: List[LyricSection] = []
        text_lines = [l.strip() for l in content.strip().split("\n") if l.strip()]

        current_section: Optional[LyricSection] = None
        current = 0.0
        line_idx = 0

        for text in text_lines:
            section = _parse_section_marker(text)
            if section is not None:
                current_section = section
                sections.append(section)
                continue

            end = current + default_duration
            words = self._make_words(text, current, end)
            lines.append(LyricLine(index=line_idx, text=text, start=current, end=end, words=words, section=current_section))
            line_idx += 1
            current = end

        return lines, sections

    @staticmethod
    def _srt_to_seconds(h: int, m: int, s: int, ms: int) -> float:
        return h * 3600 + m * 60 + s + ms / 1000.0

    @staticmethod
    def _make_words(text: str, start: float, end: float) -> List[LyricWord]:
        tokens = text.split()
        if not tokens:
            return []
        per_word = (end - start) / len(tokens)
        return [
            LyricWord(text=t, start=start + i * per_word, end=start + (i + 1) * per_word)
            for i, t in enumerate(tokens)
        ]
