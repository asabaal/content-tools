from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class BeatInfo:
    times: np.ndarray
    tempo: float
    confidence: float

    def get_nearest_beat(self, time: float) -> Tuple[float, int]:
        if len(self.times) == 0:
            return 0.0, 0
        idx = int(np.argmin(np.abs(self.times - time)))
        return float(self.times[idx]), idx

    def is_on_beat(self, time: float, tolerance: float = 0.05) -> bool:
        if len(self.times) == 0:
            return False
        nearest, _ = self.get_nearest_beat(time)
        return abs(time - nearest) <= tolerance

    def to_dict(self) -> dict:
        return {
            "times": self.times.tolist(),
            "tempo": self.tempo,
            "confidence": self.confidence,
        }


@dataclass
class FrequencyBands:
    bass: float
    low_mid: float
    mid: float
    high_mid: float
    high: float

    def get_dominant_band(self) -> str:
        bands = {"bass": self.bass, "low_mid": self.low_mid, "mid": self.mid, "high_mid": self.high_mid, "high": self.high}
        return max(bands, key=bands.get)

    def get_energy_level(self) -> float:
        return min((self.bass + self.low_mid + self.mid + self.high_mid + self.high) / 5.0, 1.0)


@dataclass
class StemFeatures:
    stem_type: str
    name: str
    energy: float = 0.0
    onset_count: int = 0

    def to_dict(self) -> dict:
        return {"stem_type": self.stem_type, "name": self.name, "energy": self.energy, "onset_count": self.onset_count}


@dataclass
class AudioFeatures:
    duration: float
    sample_rate: int
    beats: BeatInfo
    onset_times: np.ndarray
    rms_energy: np.ndarray
    spectral_centroids: np.ndarray
    zero_crossing_rate: np.ndarray
    hop_length: int = 512
    n_fft: int = 2048
    stem_features: List[StemFeatures] = None
    midi_tempo: float = None

    @property
    def frame_rate(self) -> float:
        return len(self.rms_energy) / self.duration if self.duration > 0 else 0.0

    def get_features_at_time(self, time: float) -> dict:
        if self.duration <= 0:
            return {"rms_energy": 0.0, "spectral_centroid": 0.0, "zero_crossing_rate": 0.0, "is_onset": False, "on_beat": False}
        idx = int(time * self.frame_rate)
        idx = min(idx, len(self.rms_energy) - 1)
        return {
            "rms_energy": float(self.rms_energy[idx]),
            "spectral_centroid": float(self.spectral_centroids[idx]),
            "zero_crossing_rate": float(self.zero_crossing_rate[idx]),
            "is_onset": self._is_onset(time),
            "on_beat": self.beats.is_on_beat(time),
        }

    def _is_onset(self, time: float, tolerance: float = 0.025) -> bool:
        if len(self.onset_times) == 0:
            return False
        return bool(np.min(np.abs(self.onset_times - time)) <= tolerance)

    def to_dict(self) -> dict:
        d = {
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "bpm": self.beats.tempo,
            "beat_confidence": self.beats.confidence,
            "beat_times": self.beats.times.tolist(),
            "onset_times": self.onset_times.tolist(),
            "rms_energy": self.rms_energy.tolist(),
            "spectral_centroids": self.spectral_centroids.tolist(),
            "zero_crossing_rate": self.zero_crossing_rate.tolist(),
            "frame_rate": self.frame_rate,
            "hop_length": self.hop_length,
            "n_fft": self.n_fft,
        }
        if self.midi_tempo is not None:
            d["midi_tempo"] = self.midi_tempo
        if self.stem_features:
            d["stem_features"] = [s.to_dict() for s in self.stem_features]
        return d
