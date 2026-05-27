from __future__ import annotations

import math
import random as _random
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Tuple


class AnimationType(Enum):
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_IN = "slide_in"
    SLIDE_OUT = "slide_out"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    ROTATE_IN = "rotate_in"
    TYPEWRITER = "typewriter"
    BOUNCE_IN = "bounce_in"
    ELASTIC_IN = "elastic_in"
    WAVE = "wave"
    SHAKE = "shake"
    GLOW_PULSE = "glow_pulse"


class AnimationEasing(Enum):
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"


@dataclass
class AnimationState:
    position: Tuple[float, float] = (0.0, 0.0)
    scale: Tuple[float, float] = (1.0, 1.0)
    rotation: float = 0.0
    opacity: float = 1.0
    char_progress: float = 1.0


def ease_linear(t: float) -> float:
    return t


def ease_in_quad(t: float) -> float:
    return t * t


def ease_out_quad(t: float) -> float:
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def ease_bounce(t: float) -> float:
    if t < 0.363636:
        return 7.5625 * t * t
    elif t < 0.727272:
        t -= 0.545454
        return 7.5625 * t * t + 0.75
    elif t < 0.909090:
        t -= 0.818181
        return 7.5625 * t * t + 0.9375
    else:
        t -= 0.954545
        return 7.5625 * t * t + 0.984375


def ease_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    p = 0.3
    s = p / 4
    return pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1


def ease_back(t: float) -> float:
    s = 1.70158
    return t * t * ((s + 1) * t - s)


_EASING_MAP: dict[AnimationEasing, Callable[[float], float]] = {
    AnimationEasing.LINEAR: ease_linear,
    AnimationEasing.EASE_IN: ease_in_quad,
    AnimationEasing.EASE_OUT: ease_out_quad,
    AnimationEasing.EASE_IN_OUT: ease_in_out_quad,
    AnimationEasing.BOUNCE: ease_bounce,
    AnimationEasing.ELASTIC: ease_elastic,
    AnimationEasing.BACK: ease_back,
}


def get_easing_function(easing: AnimationEasing) -> Callable[[float], float]:
    return _EASING_MAP.get(easing, ease_linear)


def _default_start_pos(animation_type: AnimationType, width: int = 0, height: int = 0) -> Tuple[float, float]:
    if animation_type == AnimationType.SLIDE_IN:
        if width > 0:
            return (float(width), 0.0)
        return (300.0, 0.0)
    if animation_type == AnimationType.SLIDE_OUT:
        return (0.0, 0.0)
    if animation_type == AnimationType.BOUNCE_IN:
        if height > 0:
            return (0.0, float(height) * 0.3)
        return (0.0, 100.0)
    return (0.0, 0.0)


def calculate_animation_state(
    animation_type: AnimationType,
    progress: float,
    easing: AnimationEasing = AnimationEasing.EASE_OUT,
    start_pos: Tuple[float, float] = None,
    target_pos: Tuple[float, float] = (0, 0),
    amplitude: float = 1.0,
    width: int = 0,
    height: int = 0,
) -> AnimationState:
    if start_pos is None:
        start_pos = _default_start_pos(animation_type, width, height)
    eased = get_easing_function(easing)(progress)
    state = AnimationState()

    if animation_type == AnimationType.FADE_IN:
        state.opacity = eased
        state.position = target_pos

    elif animation_type == AnimationType.FADE_OUT:
        state.opacity = 1.0 - eased
        state.position = target_pos

    elif animation_type == AnimationType.SLIDE_IN:
        state.position = (
            start_pos[0] + (target_pos[0] - start_pos[0]) * eased,
            start_pos[1] + (target_pos[1] - start_pos[1]) * eased,
        )
        state.opacity = min(progress * 2.5, 1.0)

    elif animation_type == AnimationType.SLIDE_OUT:
        end_x = target_pos[0] + (target_pos[0] - start_pos[0])
        end_y = target_pos[1] + (target_pos[1] - start_pos[1])
        state.position = (
            target_pos[0] + (end_x - target_pos[0]) * eased,
            target_pos[1] + (end_y - target_pos[1]) * eased,
        )
        state.opacity = 1.0 - eased * 0.8

    elif animation_type == AnimationType.SCALE_IN:
        state.scale = (eased, eased)
        state.position = target_pos
        state.opacity = eased

    elif animation_type == AnimationType.SCALE_OUT:
        scale = 1.0 + (amplitude - 1.0) * eased
        state.scale = (scale, scale)
        state.position = target_pos
        state.opacity = 1.0 - eased

    elif animation_type == AnimationType.ROTATE_IN:
        state.rotation = 360 * (1.0 - eased) * amplitude
        state.position = target_pos
        state.opacity = eased

    elif animation_type == AnimationType.TYPEWRITER:
        state.char_progress = eased
        state.position = target_pos

    elif animation_type == AnimationType.BOUNCE_IN:
        bp = ease_bounce(progress)
        state.scale = (bp, bp)
        state.position = target_pos
        state.opacity = min(progress * 2, 1.0)

    elif animation_type == AnimationType.ELASTIC_IN:
        ep = ease_elastic(progress)
        state.scale = (ep, ep)
        state.position = target_pos
        state.opacity = min(progress * 3, 1.0)

    elif animation_type == AnimationType.WAVE:
        wave_offset = math.sin(progress * math.pi * 2 * amplitude) * 30
        state.position = (target_pos[0], target_pos[1] + wave_offset)

    elif animation_type == AnimationType.SHAKE:
        rng = _random.Random(int(progress * 10000))
        shake_x = rng.uniform(-10, 10) * amplitude
        shake_y = rng.uniform(-10, 10) * amplitude
        state.position = (target_pos[0] + shake_x, target_pos[1] + shake_y)

    elif animation_type == AnimationType.GLOW_PULSE:
        state.position = target_pos
        state.opacity = 0.5 + 0.5 * math.sin(progress * math.pi * 2 * amplitude)

    return state


def interpolate_states(
    state1: AnimationState, state2: AnimationState, blend: float
) -> AnimationState:
    return AnimationState(
        position=(
            state1.position[0] + (state2.position[0] - state1.position[0]) * blend,
            state1.position[1] + (state2.position[1] - state1.position[1]) * blend,
        ),
        scale=(
            state1.scale[0] + (state2.scale[0] - state1.scale[0]) * blend,
            state1.scale[1] + (state2.scale[1] - state1.scale[1]) * blend,
        ),
        rotation=state1.rotation + (state2.rotation - state1.rotation) * blend,
        opacity=state1.opacity + (state2.opacity - state1.opacity) * blend,
        char_progress=state1.char_progress
        + (state2.char_progress - state1.char_progress) * blend,
    )
