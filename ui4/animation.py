import inspect

from contextlib import contextmanager
from dataclasses import asdict
from dataclasses import dataclass
from math import inf
from typing import Optional

from ui4.constants import *


DEFAULT_DURATION = 0.3  # seconds

@dataclass
class AnimationSpec:
    duration: float = DEFAULT_DURATION
    ease: str = None
    start_delay: float = None
    end_delay: float = None
    direction: str = None
    iterations: float = None
    
    def merge(self, other_dict):
        new_dict = asdict(self)
        new_dict.update({
            key: value
            for key, value in other_dict.items()
            if not value is None
        })
        return AnimationSpec(**new_dict)
        
    @property
    def defined_values(self):
        return {
            key: value
            for key, value in asdict(self).items()
            if not value is None
        }
        
        
_ui4_animation_context_variable = '_ui4_animation_context_variable'
        
        
def _animation(**kwargs):
    frame = inspect.currentframe().f_back.f_back
    animation_specs = frame.f_locals.get(_ui4_animation_context_variable, [])
    prev_spec = animation_specs and animation_specs[-1] or AnimationSpec()
    spec = prev_spec.merge(kwargs)
    animation_specs.append(spec)
    frame.f_locals[_ui4_animation_context_variable] = animation_specs

    yield
    
    animation_specs.pop()
    if not animation_specs:
        del frame.f_locals[_ui4_animation_context_variable]
        
        
@contextmanager
def animation(
    duration=DEFAULT_DURATION,
    ease=None,
    start_delay=None,
    end_delay=None,
    direction=None,
    iterations=None,
):
    iterations = iterations == FOREVER and inf or iterations
    return _animation(
        duration=duration,
        ease=ease,
        start_delay=start_delay,
        end_delay=end_delay,
        direction=direction,
        iterations=iterations,
    )


@contextmanager
def duration(duration=DEFAULT_DURATION):
    return _animation(duration=duration)
    
    
@contextmanager
def ease(ease_func=EASE_IN_OUT):
    return _animation(ease=ease_func)
    
    
@contextmanager
def start_delay(start_delay=0.3):
    return _animation(start_delay=start_delay)
    
    
@contextmanager
def end_delay(end_delay=0.3):
    return _animation(end_delay=end_delay)
    
    
@contextmanager
def direction(direction):
    return _animation(direction=direction)
    
    
@contextmanager
def iterations(iterations):
    iterations = iterations == FOREVER and inf or iterations
    return _animation(iterations=iterations)
    
    
def _animation_context() -> Optional[AnimationSpec]:
    frame = inspect.currentframe()
    while frame:
        animation_specs = frame.f_locals.get(_ui4_animation_context_variable)
        if animation_specs:
            return animation_specs[-1]
        frame = frame.f_back
    return None


_animation_key_order = (
    "duration ease start_delay end_delay direction iterations"
).split()

def _animation_short_keys(animation):
    result = {}

    for i, key in enumerate(_animation_key_order):
        value = getattr(animation, key)
        if not value is None:
            result[f'a{i+7}'] = value
            
    return result

