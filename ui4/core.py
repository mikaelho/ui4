"""
Contains behind-the-scenes machinery that all views share.
"""

import inspect
import json
import uuid

from collections.abc import Sequence
from contextlib import contextmanager
from functools import partial
from numbers import Number
from pathlib import Path
from string import Template
from types import GeneratorType
from weakref import WeakSet
from weakref import WeakValueDictionary

from ui4.color import Color


def prop(func):
    return property(func, func)


def current_user_id():
    return 'c7d7ab3a-7ea1-46ab-8517-fe7cf9672fc7'
    

class Identity:
    """
    Contains logic for view identity.
    """
    _id_counter = {}
    _views = {}
    get_user_id = current_user_id

    def __init__(self, **kwargs):
        user_id = Identity.get_user_id()
        self.id = self._get_next_id()
        Identity._views.setdefault(
            user_id, WeakValueDictionary()
        )[self.id] = self
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _get_next_id(self):
        user_id = Identity.get_user_id()
        id_counter = Identity._id_counter.setdefault(user_id, 0)
        id_counter += 1
        Identity._id_counter[user_id] = id_counter
        view_id = f'id{id_counter}'
        return view_id
    
    @staticmethod    
    def get_view(view_id):
        user_id = Identity.get_user_id()
        views = Identity._views.get(user_id)
        return views.get(view_id)


class Hierarchy(Identity):
    """
    Contains logic for managing the hierarchy between parent and child views.
    
    Containers get special pass-through treatment unless the view is marked as chrome.
    """

    def __init__(self, parent=None, children=None, container=None, is_chrome=False, **kwargs):
        self._container = None
        self._parent = None
        self._children = list()
        self.is_chrome = is_chrome
        
        self.container = container
        
        self.parent = parent

        children = children or []
        for child in children:
            child.parent = self
            
        super().__init__(**kwargs)

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
    _template = Template(
        '<$tag id="$id" class="$viewclass" $rendered_attributes '
        '$oob hx-swap="none">$content</$tag>'
    )
    _css_class = 'view'
    _tag = 'div'
    
    def _render(self, htmx_oob=False, animation_id=None):
        """
        Renders a view, recursively rendering the child views.
        
        If htmx_oob is True, the view is marked as the "out-of-band" root
        of swapped content.

        animation_id contains the ID of the next generator step in an animation, None if no next step.
        """
        self._animation_id = animation_id

        subrendered_attributes = ' '.join([
            f"{key}='{value}'"
            for key, value
            in self._subrenderer_results().items()
        ])
        
        htmx_oob = htmx_oob and 'hx-swap-oob="true"' or ''
        
        # Must use private _children not to be fooled by a container view
        rendered_children = ''.join([
            child._render(animation_id=animation_id)
            for child in self._children
        ])
        
        return self._render_result(subrendered_attributes, htmx_oob, rendered_children)
        
    def _subrenderer_results(self):
        subrenderer_results = {}
        for renderer in self._renderers:
                subrenderer_results.update(renderer(self))
                
        subrenderer_results.update(self._additional_attributes())
        
        return subrenderer_results
        
    def _additional_attributes(self):
        return {}
        
    def _render_result(self, rendered_attributes, htmx_oob, rendered_children):
        html = self._template.safe_substitute(
            tag='div',
            id=self.id,
            viewclass=self._css_class,
            rendered_attributes=rendered_attributes,
            oob=htmx_oob,
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
    _dirties = dict()

    # Animation step generators
    _animation_generators = dict()

    def __init__(self, **kwargs):
        self._animation_id = None
        super().__init__(**kwargs)

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
        event_method = getattr(self, f'on_{event_name}', None)
        if event_method:
            animation_generator = event_method(value)
            animation_id = None
            if isinstance(animation_generator, GeneratorType):
                animation_id = Events._get_animation_loop(animation_generator)
            updates = Events._render_updates(animation_id)
            print(updates)
            return updates
        return ""

    @staticmethod
    def _process_event_loop(event_loop_id):
        animation_generator, yield_value = Events._animation_generators.pop(event_loop_id)
        if yield_value:
            ...  # Process delay here?

        animation_id = Events._get_animation_loop(animation_generator)

        updates = Events._render_updates(animation_id)
        print(updates)
        return updates

    @staticmethod
    def _get_animation_loop(animation_generator):
        animation_id = uuid.uuid4()
        try:
            yield_value = next(animation_generator)
            Events._animation_generators[animation_id] = animation_generator, yield_value
        except StopIteration:
            animation_id = None
        return animation_id

    def _mark_dirty(self):
        user_id = Identity.get_user_id()
        Events._dirties.setdefault(user_id, set()).add(self)
        
    @staticmethod
    def _get_dirties():
        user_id = Identity.get_user_id()
        return Events._dirties.get(user_id, set())
        
    @staticmethod
    def _clear_dirties():
        user_id = Identity.get_user_id()
        Events._dirties[user_id] = set()

    @staticmethod
    def _render_updates(animation_id):
        roots = Events._get_roots()
        Events._clear_dirties()

        return "".join([
            root._render(htmx_oob=True, animation_id=animation_id) for root in roots
        ])
    
    @staticmethod    
    def _get_roots():
        """
        Get root views of the subtrees that need refreshing.
        """
        roots = set()
        dirties = Events._get_dirties()
        for dirty in Events._get_dirties():
            parent = dirty.parent
            while parent:
                if parent in dirties:
                    break
                parent = parent.parent
            else:
                roots.add(dirty)
        return roots

        
    @Render._register
    def _render_events(self):
        triggers = [
            event
            for method_name, event in self._event_methods.items()
            if hasattr(self, method_name)
        ]

        trigger_str = ",".join(triggers)

        return {
            'hx-post': '/event',
            'hx-trigger': trigger_str,
        } if trigger_str else {}


class Props(Events):
    
    style = None
    _css_value_funcs = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._properties = {}
        self._css_properties = {}
        self._transitions = set()
        
    @Render._register
    def _render_props(self):
        css_properties = self._fill_from_theme()
        
        styles = ";".join([
            f"{name}:{value}"
            for name, value in css_properties.items()
        ])
        
        transitions = ",".join([
            f"{css_name} {duration}s {ease_func or 'ease'}"
            for css_name, duration, ease_func
            in sorted(list(self._transitions), key=lambda value: value[0])
        ])
        self._transitions.clear()
        
        items = ";transition:".join([
            c for c in (styles, transitions) if c
        ])
            
        if items:
            attributes = {
                'style': items,
            }
            if transitions:
                attributes['ui4anim'] = self._animation_id
            return attributes
        else:
            return {}
            
    def _fill_from_theme(self):
        css_properties = dict(self._css_properties)
        
        if not self.style:
            return css_properties
        
        for key in dir(self.style):
            if key in css_properties:
                continue
            css_spec = Props._css_value_funcs.get(key)
            if css_spec:
                css_name, css_value_func = css_spec
                value = getattr(self.style, key)
                if callable(value):
                    value = value(self.style)
                css_properties[css_name] = css_value_func(value)
        
        return css_properties
        
    def _getter(self, attribute):
        """
        Note we do not return the CSS value.
        """
        return self._properties.get(attribute)
        
    def _setter(self, attribute, value):
        if value != self._properties.get(attribute):
            self._mark_dirty()
            self._properties[attribute] = value
            
    @staticmethod
    def _prop(property_name):
        return property(
            lambda self: partial(
                Props._getter, self, property_name,
            )(),
            lambda self, value: partial(
                Props._setter, 
                self, 
                property_name, 
                value, 
            )()
        )

    def _set_css_property(
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
        

    def _css_setter(self, property_name, css_name, value, css_value_func):
        css_value = css_value_func(value)
        self._set_css_property(property_name, value, css_name, css_value)

    @staticmethod
    def _css_plain_prop(property_name, css_name):
        def css_value_func(value):
            css_value = value
            if type(css_value) in (int, float):
                css_value = f"{css_value}px"
            return css_value
        Props._css_value_funcs[property_name] = css_name, css_value_func
        return property(
            lambda self: partial(
                Props._getter, self, property_name,
            )(),
            lambda self, value: partial(
                Props._css_setter, 
                self, 
                property_name, 
                css_name, 
                value, 
                css_value_func,
            )()
        )
        
    def _css_color_setter(self, property_name, css_name, value, css_value_func):
        if not type(value) is Color:
            value = Color(value)
        css_value = css_value_func(value)
        self._set_css_property(property_name, value, css_name, css_value)

    @staticmethod
    def _css_color_prop(property_name, css_name):
        def css_value_func(value):
            return value.css
        Props._css_value_funcs[property_name] = css_name, css_value_func
        return property(
            lambda self: partial(
                Props._getter, self, property_name,
            )(),
            lambda self, value: partial(
                Props._css_color_setter, 
                self,
                property_name,
                css_name,
                value,
                css_value_func,
            )()
        )
    
    @staticmethod
    def _css_bool_prop(property_name, css_name, css_true_value):
        def css_value_func(value):
            return value and css_true_value or None
        Props._css_value_funcs[property_name] = css_name, css_value_func
        return property(
            lambda self: partial(
                Props._getter, self, property_name,
            )(),
            lambda self, value: partial(
                Props._css_setter,
                self, property_name, 
                css_name,
                value,
                css_value_func,
            )()
        )


class Anchor:
    """
    Utility class that holds the information about a single anchor.

    "Anchor" refers to a single view size & position parameter, like view.width or view.left.
    """
    
    key_order = (
        "target_attribute comparison "
        "source_view source_attribute multiplier modifier duration ease_func"
    ).split()

    def __init__(self,
                 target_view=None,
                 target_attribute=None,
                 comparison=None,
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

    def __repr__(self):
        items = ", ".join([
            f"{key}: {getattr(value, 'id', value)}"
            for key, value in zip(
                self.key_order,
                [getattr(self, key2) for key2 in self.key_order]
            )
            if value is not None
        ])
        return f"<{self.__class__.__name__} ({items})>"

    def as_dict(self, gap=None):
        """
        Returns anchor values where defined, with shortened keys.
        """
        d = {}
        for i, key in enumerate(self.key_order):
            value = getattr(self, key)
            if value is None and gap is not None and key == 'modifier':
                value = gap
            if not value is None:
                value = getattr(value, "id", value)
                d[f'a{i}'] = value
        return d
        
    def as_json(self):
        return json.dumps(
            self.as_dict(), 
            check_circular=False, 
            separators=(',', ':')
        )

    def __hash__(self):
        if self.comparison in (None, '='):
            return hash(
                f'{self.target_view and self.target_view.id}'
                f'{self.target_attribute}'
            )
        else:
            return hash(
                f'{self.target_view and self.target_view.id}'
                f'{self.target_attribute}'
                f'{self.comparison}'
                f'{self.source_view and self.source_view.id}'
                f'{self.source_attribute}'
            )

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __gt__(self, other):
        self.target_view._anchor_setter(
            self.target_attribute,
            other,
            comparison='>'
        )
        return self

    __ge__ = __gt__
                        
    def gt(self, other):
        return self.__gt__(other)
        
    ge = gt

    def __lt__(self, other):
        self.target_view._anchor_setter(
            self.target_attribute,
            other,
            comparison='<'
        )
        return self
        
    __le__ = __lt__
        
    def lt(self, other):
        return self.__lt__(other)

    le = lt

    def clear(self):
        self.target_view._constraints.difference_update({
            constraint
            for constraint in self.target_view._constraints
            if constraint.target_attribute == self.target_attribute
        })

    def __add__(self, other):
        if other is None:
            self.modifier = None
        elif self.modifier is None:
            self.modifier = other
        else:
            self.modifier += other
        return self

    def __sub__(self, other):
        return self.__add__(other and -other)

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


def _set_comparison(anchor, comparison):
    anchor.comparison = comparison
    return anchor


def eq(anchor):
    return _set_comparison(anchor, '=')


def gt(anchor):
    return _set_comparison(anchor, '>')
ge = gt


def lt(anchor):
    return _set_comparison(anchor, '<')
le = lt


class Anchors(Events):

    def __init__(self, gap=None, flow=False, **kwargs):
        self.flow = flow
        self._constraints = set()
        self._fit = False
        super().__init__(**kwargs)
        self.gap = gap
        
    gap = Props._prop('gap')
        
    @Render._register
    def _render_anchors(self):
        constraints = [
            anchor.as_dict(self.gap)
            for anchor in self._constraints
        ]
        animated = any((anchor.duration for anchor in self._constraints))
        
        if constraints:
            attributes = {
                'ui4': json.dumps(
                    constraints,
                    check_circular=False,
                    separators=(',', ':'),
                ),
            }
            if animated:
                attributes['ui4anim'] = self._animation_id
            return attributes
        else:
            return {}

    def _anchor_getter(self, attribute):
        return Anchor(target_view=self, target_attribute=attribute)

    def _anchor_setter(self, attribute, value, comparison=None):
        self._mark_dirty()
        if isinstance(value, Number):
            value = Anchor(modifier=value)
        if type(value) is Anchor:
            value.source_view = value.target_view
            value.source_attribute = value.target_attribute
            value.target_view = self
            value.target_attribute = attribute
            value.comparison = comparison or value.comparison or '='
            
            anim_context = _animation_context()
            if anim_context:
                value.duration, value.ease_func = anim_context

            self._constraints.discard(value)  # Overwrite "similar" anchor, see Anchor.__hash__
            self._constraints.add(value)

            constrained_attributes = set([anchor.target_attribute for anchor in self._constraints])
            for checklist in (
                set('left right center_x width'.split()),
                set('top bottom center_y height'.split()),
            ):
                constraints_per_dimension = constrained_attributes.intersection(checklist)
                if len(constraints_per_dimension) > 2:
                    raise RuntimeError(
                        "Too many constraints in one dimension", constraints_per_dimension
                    )
        else:
            raise TypeError(f"Cannot set {value} as {attribute}")

    @staticmethod
    def anchorprop(attribute):
        return property(
            lambda self:
                partial(Anchors._anchor_getter, self, attribute)(),
            lambda self, value:
                partial(
                    Anchors._anchor_setter,
                    self, 
                    attribute, 
                    value,
                )()
        )
    
    # Docking attributes are read-only
    @staticmethod
    def anchordock(attribute):
        return property(
            lambda self:
                partial(Anchors._anchor_getter, self, attribute)()
        )
    
    # Multi-attribute property creator
    # e.g. center = center_x + center_y
    def _anchor_multiple_getter(self, attributes):
        return [getattr(self, attribute) for attribute in attributes]

    def _anchor_multiple_setter(self, attributes, values):
        for attribute, value in zip(attributes, values):
            setattr(self, attribute, value)

    @staticmethod
    def anchorprops(*attributes):
        return property(
            lambda self:
                partial(Anchors._anchor_multiple_getter, self, attributes)(),
            lambda self, value:
                partial(
                    Anchors._anchor_multiple_setter,
                    self,
                    attributes,
                    value,
                )()
        )
        
    @prop
    def fit(self, *value):
        if value:
            value = value[0]
            self._fit = value
            if isinstance(value, Number):
                extra_width = extra_height = value
                value = True
            else:
                extra_width = extra_height = 0
            if value not in ('width', 'height', True):
                raise ValueError(f'Invalid value for fit: {value}')
            if value in ('width', True):
                setattr(self, 'width', Anchor(
                    target_view=self, 
                    target_attribute='fitWidth',
                    modifier=extra_width,
                ))
            if value in ('height', True):
                setattr(self, 'height', Anchor(
                    target_view=self, 
                    target_attribute='fitHeight',
                    modifier=extra_height,
                ))
        else:
            return self._fit
            

    @prop
    def dock(self, *value):
        if value:
            value = value[0]
            self._dock = value
            if issubclass(type(value), Sequence) and len(value) == 2:
                value = value[0]
                value.target_attribute = 'center'
            if not type(value) is Anchor:
                raise TypeError(
                    f'Dock value must be something like view.left, not {value}'
                )
            other = value.target_view
            dock_type = value.target_attribute
            dock_attributes = PARENT_DOCK_SPECS.get(dock_type)
            if dock_attributes:
                self.parent = other
                for attribute in dock_attributes:
                    setattr(
                        self,
                        attribute,
                        getattr(other, attribute)
                        * (value.multiplier or 1)
                        + value.modifier,
                    )
            else:
                dock_attributes = SIBLING_DOCK_SPECS.get(dock_type)
                if dock_attributes:
                    this, that, align, size = dock_attributes
                    self.parent = other.parent
                    setattr(
                        self, this,
                        getattr(other, that)
                        * (value.multiplier or 1)
                        + value.modifier,
                    )
                    setattr(self, align, getattr(other, align))
                    setattr(self, size, getattr(other, size))
                else:
                    raise ValueError(f'Unknown docking attribute {dock_type}')
        else:
            return self._dock


PARENT_DOCK_SPECS = {
    'top': ('top', 'left', 'right'),
    'left': ('left', 'top', 'bottom'),
    'bottom': ('bottom', 'left', 'right'),
    'right': ('right', 'top', 'bottom'),
    'top_left': ('top', 'left'),
    'top_right': ('top', 'right'),
    'bottom_left': ('bottom', 'left'),
    'bottom_right': ('bottom', 'right'),
    'center': ('center_x', 'center_y'),
    'top_center': ('top', 'center_x'),
    'bottom_center': ('bottom', 'center_x'),
    'left_center': ('left', 'center_y'),
    'right_center': ('right', 'center_y'),
    'sides': ('left', 'right'),
    'top_and_bottom': ('top', 'bottom'),
    'all': ('top', 'left', 'right', 'bottom'),
}

SIBLING_DOCK_SPECS = {
    'above': ('bottom', 'top', 'center_x', 'width'),
    'below': ('top', 'bottom', 'center_x', 'width'),
    'left_of': ('right', 'left', 'center_y', 'height'),
    'right_of': ('left', 'right', 'center_y', 'height'),
}


class Core(Anchors, Props):
    """
    This class is here simply to collect the different mechanical parts of the core view class for inheritance.
    """
    def __init__(self, text=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        
    text = Props._prop('text')
        
        
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

