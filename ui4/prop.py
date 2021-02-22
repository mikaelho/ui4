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
    from ui4.view import View
    self.__class__._dirties.add(self)
    if normalize_func:
        value = normalize_func(value)
    self._values[attribute] = value
    if to_css_func:
        value = to_css_func(value)
    self._style_values[css_attribute] = value
    if View._animated:
        self._transitions.append(css_attribute)
    
    
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
    
    
def cssprop_onoff(attribute, css_attribute, on_value, off_value='normal'):
    return property(
        lambda self:
            partial(_css_getter, self, attribute)(),
        lambda self, value:
            partial(
                _css_setter, 
                self, 
                attribute, 
                css_attribute, 
                lambda v: on_value if v else off_value, 
                None, value
            )()
    )


css = partial(cssprop, None, None)


cssprop_color = partial(
    cssprop,
    lambda value: Color(value),
    lambda value: value.css,
)

       
cssprop_px = partial(
    cssprop, None,
    lambda value: f'{value}px',
)


cssprop_bold = partial(
    cssprop, None,
    lambda value: 'bold' if value else 'normal'
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
    
    def __init__(self, comparison='=', view=None, attribute='', operator='', constant='', duration=None):
        self.comparison = comparison
        self.view = view
        self.attribute = attribute
        self.operator = operator
        self.constant = constant
        self.duration = duration
        
    def render(self, attribute):
        return (
            f'{attribute}'
            f'{self.comparison}'
            f'{self.view and self.view.id or ""}'
            f'{self.view and "." or ""}'
            f'{self.attribute}'
            f'{self.operator}'
            f'{self.constant}'
            f'{self.duration and "|" or ""}'
            f'{self.duration or ""}'
        )
        
    def clear(self):
        for comparisons in self.view._constraints.values():
            comparisons.pop(self.attribute, None)
        
    def _modify(self, operator, value):
        if self.operator:
            raise RuntimeError(f'Only 1 modifier supported')
        self.operator = operator
        self.constant = value
        
    def __add__(self, other):
        self._modify('+', other)
        return self
        
    def __sub__(self, other):
        self._modify('-', other)
        return self
        
    def __mul__(self, other):
        self._modify('*', other)
        return self
        
    def __truediv__(self, other):
        self._modify('/', other)
        return self
        
    def __mod__(self, other):
        self._modify('%', other)
        return self
            

def _ui4_getter(self, attribute):
    return Anchor('=', self, attribute)

_checklists = (
    set('left right center_x width'.split()),
    set('top bottom center_y height'.split()),
)

def _ui4_setter(self, attribute, css_attribute, value):
    from ui4.view import View
    self.__class__._dirties.add(self)
    if type(value) in (int, float):
        value = Anchor(constant=value)
    if type(value) is Anchor:
        if View._animated:
            value.duration = .3
        comparisons = self._constraints[value.comparison]
        self._style_values.pop(css_attribute, None)
        if value.comparison == '=':
            comparisons[attribute] = [value]
        else:
            comparisons.setdefault(attribute, list()).append(value)
        for checklist in _checklists:
            constraints = set(self._constraints.keys()).intersection(checklist)
            if len(constraints) > 2:
                raise RuntimeError(
                    f'Too many constraints in one dimension: {constraints}'
                )
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
