from __future__ import annotations

import random
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


class BackgroundVideoSource:
    def __init__(
        self,
        paths: List[str | Path],
        width: int = 1920,
        height: int = 1080,
        beat_times: Optional[List[float]] = None,
    ):
        self.paths = [Path(p) for p in paths]
        self.width = width
        self.height = height
        self.beat_times = beat_times or []
        self._captures: dict[int, cv2.VideoCapture] = {}
        self._clip_index = 0
        self._last_beat_idx = -1

    def _get_capture(self, idx: int) -> Optional[cv2.VideoCapture]:
        idx = idx % len(self.paths)
        if idx not in self._captures:
            path = self.paths[idx]
            if not path.exists():
                return None
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                return None
            self._captures[idx] = cap
        return self._captures[idx]

    def _current_clip_index(self, t: float) -> int:
        if not self.beat_times:
            return self._clip_index
        beat_idx = -1
        for i, bt in enumerate(self.beat_times):
            if bt <= t:
                beat_idx = i
            else:
                break
        if beat_idx >= 0 and beat_idx != self._last_beat_idx:
            self._clip_index = (self._clip_index + 1) % len(self.paths)
            self._last_beat_idx = beat_idx
        return self._clip_index

    def get_frame(self, t: float) -> Optional[np.ndarray]:
        if not self.paths:
            return None

        clip_idx = self._current_clip_index(t)
        cap = self._get_capture(clip_idx)
        if cap is None:
            return None

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_idx = int(t * fps) % int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            return None

        frame = cv2.resize(frame, (self.width, self.height))
        return frame

    def get_frame_pil(self, t: float) -> Optional[Image.Image]:
        frame = self.get_frame(t)
        if frame is None:
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame)

    def close(self) -> None:
        for cap in self._captures.values():
            cap.release()
        self._captures.clear()

    def __del__(self) -> None:
        self.close()


class BackgroundImageSource:
    def __init__(
        self,
        paths: List[str | Path],
        width: int = 1920,
        height: int = 1080,
        beat_times: Optional[List[float]] = None,
    ):
        self.paths = [Path(p) for p in paths]
        self.width = width
        self.height = height
        self.beat_times = beat_times or []
        self._images: List[Optional[np.ndarray]] = []
        self._loaded = False
        self._index = 0
        self._last_beat_idx = -1

    def _load_all(self) -> None:
        if self._loaded:
            return
        for p in self.paths:
            if p.exists():
                img = cv2.imread(str(p))
                if img is not None:
                    img = cv2.resize(img, (self.width, self.height))
                    self._images.append(img)
                else:
                    self._images.append(None)
            else:
                self._images.append(None)
        self._loaded = True

    def _current_index(self, t: float) -> int:
        if not self.beat_times or not self._images:
            return self._index % max(1, len(self._images))
        beat_idx = -1
        for i, bt in enumerate(self.beat_times):
            if bt <= t:
                beat_idx = i
            else:
                break
        if beat_idx >= 0 and beat_idx != self._last_beat_idx:
            self._index = (self._index + 1) % len(self._images)
            self._last_beat_idx = beat_idx
        return self._index % max(1, len(self._images))

    def get_frame(self, t: float) -> Optional[np.ndarray]:
        self._load_all()
        if not self._images:
            return None
        idx = self._current_index(t)
        img = self._images[idx]
        if img is None:
            available = [x for x in self._images if x is not None]
            if not available:
                return None
            img = available[0]
        return img

    def get_frame_pil(self, t: float) -> Optional[Image.Image]:
        frame = self.get_frame(t)
        if frame is None:
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame)

    def close(self) -> None:
        self._images.clear()
        self._loaded = False


def create_background_source(
    path: str | Path | List[str | Path],
    width: int = 1920,
    height: int = 1080,
    beat_times: Optional[List[float]] = None,
) -> BackgroundVideoSource | BackgroundImageSource | None:
    if isinstance(path, list):
        paths = path
    else:
        p = Path(path)
        if not p.exists():
            return None
        paths = [path]

    if not paths:
        return None

    exts = {Path(p).suffix.lower() for p in paths}
    video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    if exts & video_exts:
        return BackgroundVideoSource(paths, width, height, beat_times)
    else:
        return BackgroundImageSource(paths, width, height, beat_times)
