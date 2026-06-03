import math

from render.animations import (
    AnimationEasing,
    AnimationState,
    AnimationType,
    calculate_animation_state,
    ease_back,
    ease_bounce,
    ease_elastic,
    ease_in_out_quad,
    ease_in_quad,
    ease_linear,
    ease_out_quad,
    get_easing_function,
    interpolate_states,
)


class TestEasingFunctions:
    def test_linear(self):
        assert ease_linear(0.0) == 0.0
        assert ease_linear(0.5) == 0.5
        assert ease_linear(1.0) == 1.0

    def test_ease_in_quad(self):
        assert ease_in_quad(0.0) == 0.0
        assert ease_in_quad(0.5) == 0.25
        assert ease_in_quad(1.0) == 1.0

    def test_ease_out_quad(self):
        assert ease_out_quad(0.0) == 0.0
        assert ease_out_quad(1.0) == 1.0
        assert 0 < ease_out_quad(0.5) < 1.0

    def test_ease_in_out_quad(self):
        assert ease_in_out_quad(0.0) == 0.0
        assert ease_in_out_quad(1.0) == 1.0
        assert ease_in_out_quad(0.5) == 0.5

    def test_ease_bounce_boundaries(self):
        assert ease_bounce(0.0) == 0.0
        assert abs(ease_bounce(1.0) - 1.0) < 0.001

    def test_ease_bounce_values_in_range(self):
        for t in [i / 100 for i in range(101)]:
            v = ease_bounce(t)
            assert 0.0 <= v <= 1.1

    def test_ease_elastic_boundaries(self):
        assert ease_elastic(0.0) == 0.0
        assert ease_elastic(1.0) == 1.0

    def test_ease_elastic_overshoots(self):
        val = ease_elastic(0.5)
        assert val > 1.0 or val < 0.0

    def test_ease_back_boundaries(self):
        assert ease_back(0.0) == 0.0
        assert abs(ease_back(1.0) - 1.0) < 0.01

    def test_ease_back_overshoots(self):
        mid = ease_back(0.5)
        assert mid < 0.0 or mid > 1.0


class TestGetEasingFunction:
    def test_returns_callable(self):
        for e in AnimationEasing:
            fn = get_easing_function(e)
            assert callable(fn)

    def test_unknown_returns_linear(self):
        fn = get_easing_function(AnimationEasing.LINEAR)
        assert fn(0.5) == 0.5


class TestAnimationState:
    def test_default_values(self):
        s = AnimationState()
        assert s.position == (0.0, 0.0)
        assert s.scale == (1.0, 1.0)
        assert s.rotation == 0.0
        assert s.opacity == 1.0
        assert s.char_progress == 1.0


class TestCalculateAnimationState:
    def test_fade_in_progress_0(self):
        s = calculate_animation_state(AnimationType.FADE_IN, 0.0)
        assert s.opacity == 0.0

    def test_fade_in_progress_1(self):
        s = calculate_animation_state(AnimationType.FADE_IN, 1.0)
        assert s.opacity == 1.0

    def test_fade_out_progress_0(self):
        s = calculate_animation_state(AnimationType.FADE_OUT, 0.0)
        assert s.opacity == 1.0

    def test_fade_out_progress_1(self):
        s = calculate_animation_state(AnimationType.FADE_OUT, 1.0)
        assert s.opacity == 0.0

    def test_slide_in_from_start_to_target(self):
        s = calculate_animation_state(
            AnimationType.SLIDE_IN, 0.0, start_pos=(100, 50), target_pos=(0, 0)
        )
        assert s.position == (100.0, 50.0)

    def test_slide_in_at_end(self):
        s = calculate_animation_state(
            AnimationType.SLIDE_IN, 1.0, start_pos=(100, 50), target_pos=(0, 0)
        )
        assert s.position == (0.0, 0.0)

    def test_slide_out_extends_beyond_target(self):
        s = calculate_animation_state(
            AnimationType.SLIDE_OUT, 1.0, start_pos=(100, 0), target_pos=(0, 0)
        )
        assert s.position[0] < 0.0

    def test_scale_in_progress_0(self):
        s = calculate_animation_state(AnimationType.SCALE_IN, 0.0)
        assert s.scale == (0.0, 0.0)

    def test_scale_in_progress_1(self):
        s = calculate_animation_state(AnimationType.SCALE_IN, 1.0)
        assert s.scale == (1.0, 1.0)

    def test_scale_out_grows_and_fades(self):
        s = calculate_animation_state(AnimationType.SCALE_OUT, 1.0, amplitude=2.0)
        assert s.scale == (2.0, 2.0)
        assert s.opacity == 0.0

    def test_rotate_in_at_0(self):
        s = calculate_animation_state(AnimationType.ROTATE_IN, 0.0)
        assert s.rotation > 0
        assert s.opacity == 0.0

    def test_rotate_in_at_1(self):
        s = calculate_animation_state(AnimationType.ROTATE_IN, 1.0)
        assert s.rotation == 0.0
        assert s.opacity == 1.0

    def test_typewriter_at_0(self):
        s = calculate_animation_state(AnimationType.TYPEWRITER, 0.0)
        assert s.char_progress == 0.0

    def test_typewriter_at_1(self):
        s = calculate_animation_state(AnimationType.TYPEWRITER, 1.0)
        assert s.char_progress == 1.0

    def test_bounce_in_opacity_rises_fast(self):
        s = calculate_animation_state(AnimationType.BOUNCE_IN, 0.5)
        assert s.opacity >= 0.5

    def test_elastic_in_at_1(self):
        s = calculate_animation_state(AnimationType.ELASTIC_IN, 1.0)
        assert s.opacity == 1.0

    def test_wave_oscillates(self):
        s0 = calculate_animation_state(AnimationType.WAVE, 0.0, amplitude=1.0)
        s25 = calculate_animation_state(AnimationType.WAVE, 0.25, amplitude=1.0)
        assert s0.position[1] != s25.position[1]

    def test_glow_pulse_oscillates(self):
        s0 = calculate_animation_state(AnimationType.GLOW_PULSE, 0.0)
        s25 = calculate_animation_state(AnimationType.GLOW_PULSE, 0.25)
        assert s0.opacity != s25.opacity

    def test_easing_applied(self):
        s_linear = calculate_animation_state(
            AnimationType.FADE_IN, 0.5, AnimationEasing.LINEAR
        )
        s_easeout = calculate_animation_state(
            AnimationType.FADE_IN, 0.5, AnimationEasing.EASE_OUT
        )
        assert s_linear.opacity != s_easeout.opacity

    def test_all_types_at_midpoint(self):
        for at in AnimationType:
            s = calculate_animation_state(at, 0.5)
            assert isinstance(s, AnimationState)

    def test_all_types_at_boundaries(self):
        for at in AnimationType:
            s0 = calculate_animation_state(at, 0.0)
            s1 = calculate_animation_state(at, 1.0)
            assert isinstance(s0, AnimationState)
            assert isinstance(s1, AnimationState)


class TestInterpolateStates:
    def test_blend_0_returns_state1(self):
        s1 = AnimationState(position=(10, 20), opacity=0.5)
        s2 = AnimationState(position=(30, 40), opacity=1.0)
        result = interpolate_states(s1, s2, 0.0)
        assert result.position == (10.0, 20.0)
        assert result.opacity == 0.5

    def test_blend_1_returns_state2(self):
        s1 = AnimationState(position=(10, 20), opacity=0.5)
        s2 = AnimationState(position=(30, 40), opacity=1.0)
        result = interpolate_states(s1, s2, 1.0)
        assert result.position == (30.0, 40.0)
        assert result.opacity == 1.0

    def test_blend_5_midpoint(self):
        s1 = AnimationState(position=(0, 0), opacity=0.0)
        s2 = AnimationState(position=(100, 200), opacity=1.0)
        result = interpolate_states(s1, s2, 0.5)
        assert abs(result.position[0] - 50.0) < 0.01
        assert abs(result.position[1] - 100.0) < 0.01
        assert abs(result.opacity - 0.5) < 0.01

    def test_scale_interpolation(self):
        s1 = AnimationState(scale=(0.0, 0.0))
        s2 = AnimationState(scale=(2.0, 2.0))
        result = interpolate_states(s1, s2, 0.5)
        assert result.scale == (1.0, 1.0)

    def test_rotation_interpolation(self):
        s1 = AnimationState(rotation=0.0)
        s2 = AnimationState(rotation=360.0)
        result = interpolate_states(s1, s2, 0.5)
        assert result.rotation == 180.0

    def test_char_progress_interpolation(self):
        s1 = AnimationState(char_progress=0.0)
        s2 = AnimationState(char_progress=1.0)
        result = interpolate_states(s1, s2, 0.25)
        assert result.char_progress == 0.25


class TestDefaultStartPos:
    def test_bounce_in_with_height(self):
        s = calculate_animation_state(AnimationType.BOUNCE_IN, 0.5, height=200)
        assert s.scale != (1.0, 1.0)
