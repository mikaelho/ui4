from ui4.animation import *
from ui4.animation import _animation_context

def test_merge():
    spec = AnimationSpec(1, "ease", 2, 3, "reverse", 4)
    updated_spec = spec.merge({
        "ease": "ease-in-out",
        "iterations": 5,
    })
    assert asdict(updated_spec) == {
        "duration": 1,
        "ease": "ease-in-out",
        "start_delay": 2,
        "end_delay": 3,
        "direction": "reverse",
        "iterations": 5,
    }


def test_defined_values():
    spec = AnimationSpec(
        ease="ease",
        direction="reverse",
        iterations=2,
    )
    assert spec.defined_values == {
        "duration": 0.3,
        "ease": "ease",
        "direction": "reverse",
        "iterations": 2,
    }


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
