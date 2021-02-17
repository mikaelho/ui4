from collections.abc import Sequence
from functools import partial

from ui4.color import Color


# Basic gettersetter property creator
def prop(func):
    return property(func, func)
    
prop.none = object()
    
  
# CSS property creator
# Convert to CSS, but not back
        
def _css_getter(self, attribute):
    return self._values.get(attribute)


def _css_setter(self, attribute, css_attribute, to_css_func, normalize_func, value):
    self._dirty = True
    if normalize_func:
        value = normalize_func(value)
    self._values[attribute] = value
    if to_css_func:
        value = to_css_func(value)
    self._style_values[css_attribute] = value
    
    
def cssprop(normalize_func, to_css_func, attribute, css_attribute):
    return property(
        lambda self:
            partial(_css_getter, self, attribute)(),
        lambda self, value:
            partial(
                _css_setter, 
                self, 
                attribute, 
                css_attribute, 
                to_css_func, 
                normalize_func, value
            )()
    )


cssprop_color = partial(
    cssprop,
    lambda value: Color(value),
    lambda value: value.css,
)
        
cssprop_px = partial(
    cssprop,
    None,
    lambda value: f'{value}px',
)

def _process_value(value):
    if type(value) == str:
        return value
    elif issubclass(type(value), Sequence):
        return " ".join([f"{component}px" for component in value])
    elif type(value) in (int, float):
        return f"{value}px"

cssprop_px_or_str = partial(
    cssprop,
    None,
    _process_value,
)


# ui4 constraint property creator
# Write-only layout constraints

class Anchor:
    
    def __init__(self, comparison='=', view=None, attribute='', operator='', constant=''):
        self.comparison = comparison
        self.view = view
        self.attribute = attribute
        self.operator = operator
        self.constant = constant
        
    def __str__(self):
        return (
            f'{self.comparison}'
            f'{self.view and self.view.id or ""}'
            f'{self.view and "." or ""}'
            f'{self.attribute}'
            f'{self.operator}'
            f'{self.constant}'
        )

def _ui4_getter(self, attribute):
    return Anchor('=', self, attribute)


def _ui4_setter(self, attribute, css_attribute, value):
    self._dirty = True
    if type(value) in (int, float):
        value = Anchor(constant=value)
        
        '''
        if css_attribute:
            _css_setter(self, attribute, css_attribute, lambda value: f'{value}px', None, value)
        else:
            raise TypeError(f"Cannot set a plain number value to {attribute}")
        '''
    if type(value) is Anchor:
        self._style_values.pop(css_attribute, None)
        self._constraints.setdefault(attribute, list()).append(value)
    else:
        raise TypeError(f"Cannot set {value} as {attribute}")

def ui4prop(attribute, css_attribute=True):
    return property(
        lambda self:
            partial(_ui4_getter, self, attribute)(),
        lambda self, value:
            partial(
                _ui4_setter, 
                self, 
                attribute, 
                css_attribute, 
                value,
            )()
    )
    
# Additional docking attributes are read-only
    
def ui4dock(attribute):
    return property(
        lambda self:
            partial(_ui4_getter, self, attribute)()
    )
    
    
# Multi-attribute property creator
    
def _ui4_multiple_getter(self, attributes):
    return [getattr(self, attribute) for attribute in attributes]


def _ui4_multiple_setter(self, attributes, values):
    for attribute, value in zip(attributes, values):
        setattr(self, attribute, value)


def ui4props(*attributes):
    return property(
        lambda self:
            partial(_ui4_multiple_getter, self, attributes)(),
        lambda self, value:
            partial(
                _ui4_multiple_setter, 
                self, 
                attributes, 
                value,
            )()
    )
