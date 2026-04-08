"""Animation frame generators for animate mode.

All animation types operate on the entire background as a continuous field G(x, y, t).
Every pixel changes smoothly over time. No discrete shapes, overlays, or partial regions.
"""

import math
import random
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from src.config.defaults import AnimType

if TYPE_CHECKING:
    from PIL import Image


class AnimationFrameGenerator:
    """Generates animated background frames for a given animation type."""

    def __init__(
        self,
        anim_type: AnimType,
        intensity: float,
        speed: float,
        width: int,
        height: int,
        seed: int | None = None,
        gradient_colors: list[str] | None = None,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: width={width}, height={height}")
        if speed <= 0:
            raise ValueError(f"Speed must be positive, got {speed}")
        self.anim_type = anim_type
        self.intensity = max(0.0, min(0.5, intensity))
        self.speed = speed
        self.width = width
        self.height = height
        self.gradient_colors = gradient_colors or ["#4A90E2", "#2C3E50"]
        self._seed = seed

        if seed is not None:
            self._rng = random.Random(seed)
        else:
            self._rng = random.Random()

        self._parsed_colors = [self._hex_to_rgb(c) for c in self.gradient_colors]

        self._yy, self._xx = np.mgrid[0:height, 0:width].astype(np.float64)

        self._noise_grid_a = self._make_noise_grid(32, 32)
        self._noise_grid_b = self._make_noise_grid(32, 32)
        self._noise_grid_c = self._make_noise_grid(32, 32)
        self._noise_grid_d = self._make_noise_grid(32, 32)
        self._noise_grid_e = self._make_noise_grid(32, 32)

        self._diagonal = math.sqrt(self.width**2 + self.height**2)
        self._color_array = np.array(self._parsed_colors, dtype=np.float64)
        self._num_colors = len(self._color_array)

        self._base_gradient = self._compute_gradient(self._xx, self._yy)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color '{hex_color}', expected 6 hex digits")
        try:
            return (
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
            )
        except ValueError:
            raise ValueError(f"Invalid hex color '#{hex_color}', contains non-hex characters")

    def _make_noise_grid(self, rows: int, cols: int) -> NDArray[np.float64]:
        grid = np.zeros((rows, cols), dtype=np.float64)
        for r in range(rows):
            for c in range(cols):
                grid[r, c] = self._rng.random() * 2.0 - 1.0
        return grid

    def _smooth_noise(
        self,
        xx: NDArray[np.float64],
        yy: NDArray[np.float64],
        t: float,
        grid: NDArray[np.float64],
        scale: float = 128.0,
    ) -> NDArray[np.float64]:
        rows_g, cols_g = grid.shape

        sx = (xx / scale + t * 0.5) % cols_g
        sy = (yy / scale) % rows_g

        ix = np.floor(sx).astype(np.intp)
        iy = np.floor(sy).astype(np.intp)
        fx = sx - ix
        fy = sy - iy

        ix0 = ix % cols_g
        iy0 = iy % rows_g
        ix1 = (ix + 1) % cols_g
        iy1 = (iy + 1) % rows_g

        v00 = grid[iy0, ix0]
        v10 = grid[iy0, ix1]
        v01 = grid[iy1, ix0]
        v11 = grid[iy1, ix1]

        top = v00 * (1 - fx) + v10 * fx
        bot = v01 * (1 - fx) + v11 * fx
        return top * (1 - fy) + bot * fy

    def _compute_gradient(
        self,
        xx: NDArray[np.float64],
        yy: NDArray[np.float64],
        brightness: float = 1.0,
    ) -> NDArray[np.float64]:
        """Compute gradient colors at arbitrary (x,y) coordinates analytically.

        Uses a ping-pong (triangle wave) pattern on the diagonal gradient
        parameter so the result is inherently seamless.
        """
        t = (xx / self._diagonal + yy / self._diagonal) % 1.0
        t = 1.0 - np.abs(2.0 * t - 1.0)

        scaled_t = t * (self._num_colors - 1)
        idx = np.floor(scaled_t).astype(np.intp)
        frac = scaled_t - idx
        idx = np.clip(idx, 0, self._num_colors - 2)
        frac = np.clip(frac, 0.0, 1.0)

        c1 = self._color_array[idx]
        c2 = self._color_array[idx + 1]
        frac3 = frac[:, :, np.newaxis]
        result = (c1 + (c2 - c1) * frac3) * brightness
        return result

    def _to_image(self, arr: NDArray[np.float64]) -> "Image.Image":
        from PIL import Image

        clamped = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(clamped)

    def generate_background_frame(self, t: float) -> "Image.Image":
        import logging
        logger = logging.getLogger(__name__)

        dispatch = {
            "drift": self._generate_drift,
            "flow": self._generate_flow,
            "pulse": self._generate_pulse,
            "distortion": self._generate_distortion,
            "parallax": self._generate_parallax,
            "reactive": self._generate_pulse,
        }
        if self.anim_type == "reactive":
            logger.warning("'reactive' animation mode is not yet implemented, falling back to 'pulse'")
        handler = dispatch.get(self.anim_type, self._generate_drift)
        return handler(t)

    def _generate_drift(self, t: float) -> "Image.Image":
        dx = t * self.speed * self.width * self.intensity
        dy = t * self.speed * self.height * self.intensity * 0.5
        result = self._compute_gradient(self._xx + dx, self._yy + dy)
        return self._to_image(result)

    def _generate_flow(self, t: float) -> "Image.Image":
        ts = t * self.speed
        n_y = self._smooth_noise(self._xx, self._yy, ts, self._noise_grid_a, scale=80.0)
        n_x = self._smooth_noise(self._xx, self._yy, ts * 0.7, self._noise_grid_d, scale=90.0)
        shift_y = n_y * self.intensity * self.height * 0.4
        shift_x = n_x * self.intensity * self.width * 0.25
        result = self._compute_gradient(self._xx + shift_x, self._yy + shift_y)

        color_a = self._smooth_noise(self._xx, self._yy, ts * 1.3, self._noise_grid_b, scale=100.0)
        color_b = self._smooth_noise(self._xx, self._yy, ts * 0.9, self._noise_grid_e, scale=55.0)
        color_noise = color_a * 0.6 + color_b * 0.4
        result = result + color_noise[:, :, np.newaxis] * self.intensity * 30.0
        return self._to_image(result)

    def _generate_pulse(self, t: float) -> "Image.Image":
        brightness_scale = 1.0 + math.sin(t * self.speed * 2 * math.pi) * self.intensity * 0.2
        result = self._base_gradient * brightness_scale
        return self._to_image(result)

    def _generate_distortion(self, t: float) -> "Image.Image":
        amp = self.intensity * max(self.width, self.height) * 0.12
        ts = t * self.speed
        dx = (
            self._smooth_noise(self._xx, self._yy, ts, self._noise_grid_a, scale=80.0) * 0.55
            + self._smooth_noise(self._xx, self._yy, ts * 1.7, self._noise_grid_c, scale=40.0)
            * 0.30
            + self._smooth_noise(self._xx, self._yy, ts * 2.3, self._noise_grid_e, scale=25.0)
            * 0.15
        ) * amp
        dy = (
            self._smooth_noise(
                self._xx + 50.0, self._yy + 50.0, ts * 0.8, self._noise_grid_b, scale=80.0
            )
            * 0.55
            + self._smooth_noise(
                self._xx + 50.0, self._yy + 50.0, ts * 1.5, self._noise_grid_d, scale=40.0
            )
            * 0.30
            + self._smooth_noise(
                self._xx + 50.0, self._yy + 50.0, ts * 2.1, self._noise_grid_e, scale=25.0
            )
            * 0.15
        ) * amp
        base_dx = t * self.speed * self.intensity * self.width * 0.06
        base_dy = t * self.speed * self.intensity * self.height * 0.04
        result = self._compute_gradient(self._xx + dx + base_dx, self._yy + dy + base_dy)
        return self._to_image(result)

    def _generate_parallax(self, t: float) -> "Image.Image":
        layer_speeds = [0.3, 0.6, 1.0]
        layer_weights = np.array([0.50, 0.30, 0.20], dtype=np.float64)

        result = np.zeros((self.height, self.width, 3), dtype=np.float64)

        for i, spd in enumerate(layer_speeds):
            dx = t * self.speed * spd * self.width * self.intensity * 0.4 * (1.0 + i * 0.3)
            dy = t * self.speed * spd * self.height * self.intensity * 0.3 * (0.8 + i * 0.2)
            layer = self._compute_gradient(self._xx + dx, self._yy + dy)
            result += layer * layer_weights[i]

        return self._to_image(result)
