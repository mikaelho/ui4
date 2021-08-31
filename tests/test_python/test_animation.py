from ui4.animation import *
from ui4.animation import _animation_context


def test_render():
    spec = AnimationSpec(1, "ease", 2, 3, "reverse", 4)

    assert spec.render() == '1s,ease,reverse,2s,3s,4'


def test_merge():
    spec = AnimationSpec(1, "ease", 2, 3, "reverse", 4)
    updated_spec = spec.merge({
        "ease": "ease-in-out",
        "iterations": 5,
    })

    assert updated_spec.render() == '1s,ease-in-out,reverse,2s,3s,5'


def test_animation_contextmanager():
    assert _animation_context() is None

    with animation(0.3):
        assert _animation_context().duration == 0.3

        with animation(1.0, 'foobar'):
            assert _animation_context().duration == 1.0
            assert _animation_context().ease == 'foobar'

        assert _animation_context().duration == 0.3
        assert _animation_context().ease is None

    assert _animation_context() is None


def test_dedicated_contextmanagers():
    assert _animation_context() is None

    with duration():
        assert _animation_context().duration == 0.3

    with duration(3):
        assert _animation_context().duration == 3

    with ease():
        assert _animation_context().ease == "ease-in-out"

    with ease("ease"):
        assert _animation_context().ease == "ease"

    with start_delay():
        assert _animation_context().start_delay == 0.3

    with end_delay():
        assert _animation_context().end_delay == 0.3

    with direction("alternate"):
        assert _animation_context().direction == "alternate"

    with iterations(3):
        assert _animation_context().iterations == 3
