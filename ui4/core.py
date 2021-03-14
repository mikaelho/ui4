"""
Contains behind-the-scenes machinery that all views share.
"""

import inspect

from contextlib import contextmanager
from functools import partial
from numbers import Number
from pathlib import Path
from string import Template
from types import GeneratorType
from types import SimpleNamespace
from weakref import WeakValueDictionary

from ui4.color import Color
from ui4.theme import DefaultTheme


def prop(func):
    return property(func, func)


class Identity:
    """
    Contains logic for view identity.
    """
    _id_counter = 0
    views = WeakValueDictionary()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = self._get_id()

    def _get_id(self):
        Identity._id_counter += 1
        view_id = f'id{Identity._id_counter}'
        Identity.views[view_id] = self
        return view_id

    @classmethod
    def __getitem__(cls, item):
        return Identity.views[item]


class Hierarchy(Identity):
    """
    Contains logic for managing the hierarchy between parent and child views.
    
    Containers get special pass-through treatment unless the view is marked as chrome.
    """

    def __init__(self, parent=None, children=None, container=None, is_chrome=False, **kwargs):
        super().__init__(**kwargs)
        self._container = None
        self._parent = None
        self._children = list()
        self.is_chrome = is_chrome
        
        self.container = container
        
        self.parent = parent

        children = children or []
        for child in children:
            child.parent = self

    @prop
    def parent(self, *value):
        if value:
            new_parent = value[0]
            if (
                hasattr(new_parent, 'container') and
                new_parent.container and
                not self.is_chrome
            ):
                new_parent = new_parent.container
            if self._parent:
                self._parent._children.remove(self)
            self._parent = new_parent
            if self._parent and self not in self._parent._children:
                self._parent._children.append(self)
        else:
            if self._parent and self._parent.is_container:
                return self._parent._parent
            return self._parent

    @property
    def children(self):
        """
        Returns an immutable sequence of the view's children, unless
        the view is a frame, in which case return its container's children.
        """
        container = getattr(self, 'container', None)
        children = container._children if container else self._children

        return tuple(children)
        
    @prop
    def container(self, *value):
        if value:
            container = value[0]
            if container:
                container.is_chrome = True
                container.parent = self
            self._container = container
        else:
            return self._container
        
    @property
    def is_container(self):
        """
        Return True if this view is a container within a frame.
        """
        return (
            self._parent and
            hasattr(self._parent, 'container') and
            self._parent.container == self
        )


class Render(Hierarchy):
    
    _renderers = []
    _render_template = 'view_template.html'
    _css_class = 'view'
    _tag = 'div'
    
    def __init__(self, text=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
    
    def _render(self, htmx_oob=False):
        """
        Renders a view, recursively rendering the child views.
        
        If htmx_oob is True, the view is marked as the "out-of-band" root
        of swapped content.
        """
        rendered_attributes = ' '.join([
            renderer(self) for renderer
            in self._renderers
        ])
        
        htmx_oob = htmx_oob and 'hx-swap-oob="true"' or ''
        
        # Must use private _children not to be fooled by a container
        rendered_children = ''.join([
            child._render()
            for child in self._children
        ])
         
        template = Template(
            (Path(__file__).parent / "static" / self._render_template).read_text()
        )
        return self._render_result(rendered_attributes, htmx_oob, rendered_children, template)
        
    def _render_result(self, rendered_attributes, htmx_oob, rendered_children,
    template):       
        html = template.safe_substitute(
            tag='div',
            id=self.id,
            viewclass=self._css_class,
            rendered_attributes=rendered_attributes,
            oob=htmx_oob,
            events='', constraints='', styles='',
            content=rendered_children or self.text or "",
        )
        
        return html
    
    @classmethod
    def _register(cls, f):
        """
        Decorator for registering additional functions for rendering.
        """
        cls._renderers.append(f)
        return f
    

class Events(Render):
    """
    Class for the mechanics of defining and responding to UI events.

    Here we respond to HTMX requests with rendered updated views. Event handlers can be generators, in which case
    we manage the dialog with the browser with custom "next" events.
    """
    # Views that have changes
    _dirties = set()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._event_generator = None

    # All known and accepted events from the front-end
    # Maps an event handler method name to JS event
    # "next" is special case, custom event that we use to trigger the 
    # next step in an event handler generator.
    _event_methods = {
        'on_change': 'change',
        'on_click': 'click',
    }

    def __call__(self, f):
        """
        Enable using instances of this class as event-handler decorators.
        Works only when the method name matches one of the predefined event handler names.
        """
        if f.__name__ in self._event_methods.keys():
            setattr(self, f.__name__, f)
        else:
            raise ValueError(
                f"{f.__name__} is not an event handler name: "
                f"{self._event_methods.keys()}"
            )
        return f

    def _process_event(self, event_name, value=None):
        if event_name == 'next' and self._event_generator:
            try:
                next(self._event_generator)
            except StopIteration:
                self._event_generator = None
        else:
            self._event_generator = None
            event_method = getattr(self, f'on_{event_name}', None)
            if event_method:
                event_generator = event_method(value)
                if isinstance(event_generator, GeneratorType):
                    next(event_generator)
                    self._event_generator = event_generator
        return self._render_updates()

    def _mark_dirty(self):
        Events._dirties.add(self)
        
    def _render_updates(self):
        roots = set()

        # Determine roots of the subtrees that need refreshing
        for dirty in Events._dirties:
            parent = dirty.parent
            while parent:
                if parent in Events._dirties:
                    continue
                parent = parent.parent
            roots.add(dirty)

        Events._dirties.clear()

        return "".join([
            root._render(oob=True) for root in roots
        ])
        
    @Render._register
    def _render_events(self):
        triggers = [
            event
            for method_name, event in self._event_methods.items()
            if hasattr(self, method_name)
        ]
        if self._event_generator:
            triggers.append('next')

        trigger_str = ",".join(triggers)

        return (
            f"hx-post='/event' "
            f"hx-trigger='{trigger_str}'"
        ) if trigger_str else ""


class Props(Events):
    
    def __init__(self, **kwargs):
        self._properties = {}
        self._css_properties = {}
        self._transitions = set()
        super().__init__(**kwargs)
        
    @Render._register
    def _render_props(self):
        styles = ";".join([
            f"{name}:{value}"
            for name, value in self._css_properties.items()
        ])
        transitions = ",".join([
            f"{css_name} {duration}s {ease_func or 'default-ease'}"
            for css_name, duration, ease_func
            in sorted(list(self._transitions), key=lambda value: value[0])
        ])
        self._transitions.clear()
        
        return ";transition:".join([
            styles, transitions,
        ])
        
    def _set_property(
        self,
        property_name,
        property_value,
        css_name=None,
        css_value=None
    ):
        self._properties[property_name] = property_value
        if css_name:
            self._css_properties[css_name] = css_value
            self._mark_dirty()
        duration, ease_function = _animation_context() or (None, None)
        if duration:
            self._transitions.add((
                css_name, duration, ease_function,
            ))
        
    def _style_getter(self, attribute):
        """
        Note we do not return the CSS value.
        """
        return self._properties.get(attribute)

    def _style_setter(self, property_name, css_name, value):
        css_value = value
        if type(css_value) in (int, float):
            css_value = f"{css_value}px"
        self._set_property(property_name, value, css_name, css_value)
        
    def _css_plain_prop(property_name, css_name):
        return property(
            lambda self: partial(
                Props._style_getter, self, property_name,
            )(),
            lambda self, value: partial(
                Props._style_setter, self, property_name, css_name, value,
            )()
        )
        
    def _style_color_setter(self, property_name, css_name, value):
        if not type(value) is Color:
            value = Color(value)
        css_value = value.css
        self._set_property(property_name, value, css_name, css_value)
        
    def _css_color_prop(property_name, css_name):
        return property(
            lambda self: partial(
                Props._style_getter, self, property_name,
            )(),
            lambda self, value: partial(
                Props._style_color_setter, self, property_name, css_name, value,
            )()
        )
    
    def _style_bool_setter(self, property_name, css_name, value, true_value):
        css_value = value and true_value or None
        self._set_property(property_name, value, css_name, css_value)
        
    def _css_bool_prop(property_name, css_name, css_true_value):
        return property(
            lambda self: partial(
                Props._style_getter, self, property_name,
            )(),
            lambda self, value: partial(
                Props._style_bool_setter, self, property_name, css_name,
                value, css_true_value,
            )()
        )


class Anchor:
    """
    Utility class that holds the information about a single anchor.

    "Anchor" refers to a single view size & position parameter, like view.width or view.left.
    """

    def __init__(self,
                 target_view=None,
                 target_attribute=None,
                 comparison='=',
                 source_view=None,
                 source_attribute=None,
                 multiplier=None,
                 modifier=None,
                 duration=None,
                 ease_func=None):
        self.target_view = target_view
        self.target_attribute = target_attribute
        self.comparison = comparison
        self.source_view = source_view
        self.source_attribute = source_attribute
        self.multiplier = multiplier
        self.modifier = modifier
        self.duration = duration
        self.ease_func = ease_func

    def as_dict(self):
        return {
            key: getattr(value, "id", value)
            for key, value in self.__dict__.items()
            if value is not None
        }

    def _update_from(self, other):
        if type(other) == Anchor:
            self.source_view = other.target_view
            self.source_attribute = other.target_attribute
            for attribute in "multiplier modifier duration ease_func".split():
                setattr(self, attribute, getattr(other, attribute))
        elif isinstance(other, Number):
            self.modifier = other
        else:
            raise TypeError("Invalid value in Anchor comparison, should be Anchor or Number", other)

    def __gt__(self, other):
        self._update_from(other)
        self.comparison = ">"
        return self

    def __ge__(self, other):
        return self.__gt__(other)

    def __lt__(self, other):
        self._update_from(other)
        self.comparison = "<"
        return self

    def __le__(self, other):
        return self.__lt__(other)

    def clear(self):
        # for comparisons in self.target_view._constraints.values():
        #    comparisons.pop(self.attribute, None)
        ...

    def __add__(self, other):
        if self.modifier is None:
            self.modifier = other
        else:
            self.modifier += other
        return self

    def __sub__(self, other):
        if self.modifier is None:
            self.modifier = -other
        else:
            self.modifier -= other
        return self

    def __mul__(self, other):
        if self.multiplier is None:
            self.multiplier = other
        else:
            self.multiplier *= other
        return self

    def __truediv__(self, other):
        if self.multiplier is None:
            self.multiplier = 1 / other
        else:
            self.multiplier /= other
        return self


class Anchors(Render):
    default_gap = 8

    def __init__(self, gap=None, flow=False, **kwargs):
        self.gap = self.default_gap if gap is None else gap
        self.halfgap = self.gap / 2
        self.flow = flow
        super().__init__(**kwargs)


class Core(Anchors, Props):
    """
    This class is here simply to collect the different mechanical parts of the core view class for inheritance.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        
_ui4_animation_context_variable = '_ui4_animation_context_variable'
        
@contextmanager
def animation(duration=0.3, ease_func=None):
    frame = inspect.currentframe().f_back.f_back
    animation_specs = frame.f_locals.get(_ui4_animation_context_variable, [])
    animation_specs.append((duration, ease_func))
    frame.f_locals[_ui4_animation_context_variable] = animation_specs

    yield
    
    animation_specs.pop()
    if not animation_specs:
        del frame.f_locals[_ui4_animation_context_variable]
    
    
def _animation_context():
    frame = inspect.currentframe()
    while frame:
        animation_specs = frame.f_locals.get(_ui4_animation_context_variable)
        if animation_specs:
            return animation_specs[-1]
        frame = frame.f_back
    return None

