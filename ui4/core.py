"""
Contains behind-the-scenes machinery that all views share.
"""
import copy
import json
import types
import uuid
from collections import defaultdict
from collections.abc import Sequence
from functools import partial
from functools import wraps
from numbers import Number
from string import Template
from types import GeneratorType

from ui4.animation import _animation_context
from ui4.animation import _animation_short_keys
from ui4.color import Color
from ui4.utils import decorator_argument_wrapper


def prop(func):
    return property(func, func)


def current_user_id():
    return 'c7d7ab3a-7ea1-46ab-8517-fe7cf9672fc7'
    

class Identity:
    """
    Contains logic for view identity.
    """
    _id_counter = defaultdict(int)
    _views = defaultdict(dict)
    get_user_id = current_user_id

    def __init__(self, **kwargs):
        user_id = Identity.get_user_id()
        self.id = self._get_next_id()
        Identity._views[user_id][self.id] = self

        self.apply(kwargs)

    def apply(self, kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def _get_next_id():
        user_id = Identity.get_user_id()
        id_counter = Identity._id_counter[user_id]
        id_counter += 1
        Identity._id_counter[user_id] = id_counter
        return f'id{id_counter}'
    
    @staticmethod    
    def get_view(view_id):
        """
        Get view object by id _for the current user_.
        """
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
    _template = Template('<$tag id="$id" $rendered_attributes $oob hx-swap="none">$content</$tag>')
    _css_class = None
    _tag = 'div'
    
    def _render(self, htmx_oob=False, animation_id=None):
        """
        Renders a view, recursively rendering the child views.
        
        If htmx_oob is True, the view is marked as the "out-of-band" root
        of swapped content.

        animation_id contains the ID of the next generator step in an animation, None if no next step.
        """
        self._animation_id = animation_id

        attributes = self._subrenderer_results()

        if self._css_class:
            attributes['class'] = self._css_class

        subrendered_attributes = ' '.join(
            f"{key}='{value}'" for key, value
            in attributes.items()
        )

        htmx_oob = htmx_oob and 'hx-swap-oob="true"' or ''

        # Must use private _children not to be fooled by a container view
        rendered_children = ''.join(
            child._render(animation_id=animation_id) for child in self._children
        )

        render_result = self._render_result(subrendered_attributes, htmx_oob, rendered_children)
        #nprint(render_result)
        return render_result
        
    def _subrenderer_results(self):
        subrenderer_results = {}
        for renderer in self._renderers:
            subrenderer_results.update(renderer(self))
                
        subrenderer_results.update(self._additional_attributes())

        return subrenderer_results
        
    def _additional_attributes(self):
        return {}
        
    def _render_result(self, rendered_attributes, htmx_oob, rendered_children):
        return self._template.safe_substitute(
            tag=self._tag,
            id=self.id,
            #viewclass=self._css_class,
            rendered_attributes=rendered_attributes,
            oob=htmx_oob,
            content=rendered_children or getattr(self, 'text', None) or '',
        )

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

    Here we respond to HTMX requests with rendered updated views.
    
    Event handlers can be generators, in which case browser gets a unique id
    that it uses to request the next step of the generator.
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
        'on_input': 'input',
        'on_load': 'load',
        # 'on_input_delay': 'input',
    }

    def __call__(self, func):
        """
        Enable using instances of this class as event-handler decorators.
        Works only when the method name matches one of the predefined event handler names,
        or one of them preceeded by the `_internal_` prefix for component-internal event handling.
        """
        if (
            func.__name__ in self._event_methods.keys() or
            func.__name__.startswith('_internal_') and func.__name__[:len('_internal_')] in self._event_methods.keys()
        ):
            setattr(self, func.__name__, func)
        else:
            raise ValueError(
                f"{func.__name__} is not an event handler name: "
                f"{self._event_methods.keys()}"
            )
        return func

    @Render._register
    def _render_events(self):
        triggers = []
        for method_name, event in self._event_methods.items():
            method = getattr(self, method_name, getattr(self, f'_internal_{method_name}', None))
            if method:
                wrapped = method.__dict__.get('__wrapped__')
                options = wrapped and wrapped.__dict__.get('event_options') or {}
                trigger_components = [event] + [f'{key}:{value}' for key, value in options.items()]
                triggers.append(' '.join(trigger_components))

        trigger_str = ",".join(triggers)

        return {
            'hx-post': '/event',
            'hx-trigger': trigger_str,
        } if trigger_str else {}

    def _process_event(self, event_name, value=None):
        animation_id = None
        for method_name in (f'_internal_on_{event_name}', f'on_{event_name}'):
            event_method = getattr(self, method_name, None)
            if event_method:
                animation_generator = event_method(value)
                animation_id = None
                if isinstance(animation_generator, GeneratorType):
                    animation_id = Events._get_animation_loop(animation_generator)

        return Events._render_updates(animation_id)

    @staticmethod
    def _process_event_loop(animation_id):
        # Get generator with the old id
        animation_generator, yield_value = Events._animation_generators.pop(
            animation_id
        )
        # Return updates with the id of next step, or None if last
        animation_id = Events._get_animation_loop(animation_generator)

        updates = Events._render_updates(animation_id)
        return updates

    @staticmethod
    def _get_animation_loop(animation_generator):
        animation_id = str(uuid.uuid4())
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

        return "".join(
            root._render(htmx_oob=True, animation_id=animation_id)
            for root in roots
        )
    
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

    def remove_event(self, event_name):
        if not event_name in self._event_methods.values():
            ValueError('Unknown event, expecting one of {",".join(self._event_methods.values())}', event_name)
        setattr(self, f'on_{event_name}', None)
        self._mark_dirty()


def set_event_options(func, **options):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    if not hasattr(func, 'event_options'):
        func.event_options = {}
    func.event_options.update(options)

    return wrapper


@decorator_argument_wrapper
def delay(func, seconds: float = 0.5):
    """
    Delay event sending. If event occurs again, start the delay again.
    """
    return set_event_options(func, delay=f'{float(seconds)}s')


# @decorator_argument_wrapper
# def queue(func, keyword: str):
#     """
#     Manage handling of events that repeat before they have been handled.
#
#     Keywords: 'all', 'first', 'last' (default), 'none'
#     """
#     return set_event_options(func, queue=keyword)


class BasicProperties(Events):
    """
    Logic for handling view properties.

    Property setters can mark the view as dirty, which means that the view
    (along with children) will be rendered when next update is sent to browser.
    """
    def __init__(self, **kwargs):
        self._properties = {}
        super().__init__(**kwargs)

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
                BasicProperties._getter, self, property_name,
            )(),
            lambda self, value: partial(
                BasicProperties._setter,
                self,
                property_name,
                value,
            )()
        )


class Constraint:

    def __init__(self, value=None, initial_value=None):
        self.value = value
        self.initial_value = initial_value
        self.comparison = '='
        self.condition = None
        self.animation = None

    def __deepcopy__(self, memo):
        """
        Constraint classes can be deep copied without deep copying views and such.

        All Constraint subclasses must have an __init__ that can be called without arguments.
        """
        copied = type(self)()
        for key in dir(self):
            if key.startswith('_'):
                continue
            value = getattr(self, key)
            if type(value) == types.MethodType:
                continue
            if isinstance(value, (Constraint, dict)):
                value = copy.deepcopy(value)
            setattr(copied, key, value)
        return copied

    def __str__(self):
        return str(self.value)

    def serialize(self, target):
        serialised = f'{f"{self.condition}?" if self.condition else ""}{target}{self.comparison}{str(self)}'

        if self.animation:
            serialised = f'{serialised}:{self.animation.render()}'

        return serialised

    def walk(self, function):
        result = function(self)

        if result:
            return result

        if isinstance(self.value, Constraint):
            return self.value.walk(function)

        return False

    def get_anchor(self):
        return self.walk(lambda item: isinstance(item, ConstraintAnchor) and item)


class ConstraintExpression(Constraint):

    def __str__(self):
        if self.value is None:
            return self.initial_value
        if type(self.value) is not dict:
            return str(self.value)

        lhs = self.value['lhs']
        rhs = self.value['rhs']
        if type(lhs) is ConstraintExpression and type(lhs.value) is dict:
            lhs = f'({lhs})'
        if type(rhs) is ConstraintExpression and type(rhs.value) is dict:
            rhs = f'({rhs})'

        return f'{lhs}{self.value["operator"]}{rhs}'

    def _operator(self, operator, other):
        return ConstraintExpression({
            'operator': operator,
            'lhs': type(self) is not ConstraintExpression and self or type(self)(self.value or self.initial_value),
            'rhs': other,
        })

    def __add__(self, other):
        return self._operator('+', other)

    def __sub__(self, other):
        return self._operator('-', other)

    def __mul__(self, other):
        return self._operator('*', other)

    def __truediv__(self, other):
        return self._operator('/', other)

    def __gt__(self, other):
        return ConstraintCondition(self._operator('>', other))
    __gte__ = __gt__

    def __lt__(self, other):
        return ConstraintCondition(self._operator('<', other))
    __lte__ = __lt__

    def walk(self, function):
        result = function(self)

        if result:
            return result

        if self.value and isinstance(self.value, (Constraint, dict)):
            for component in ('lhs', 'rhs'):
                if isinstance(self.value[component], Constraint):
                    result = self.value[component].walk(function)
                    if result:
                        return result

        return False

    def invert_operator(self):
        if type(self.value) is dict and 'operator' in self.value:
            previous = self.value['operator']
            if previous in ('+', '-'):
                self.value['operator'] = previous == '+' and '-' or '+'
        return self


gap = ConstraintExpression(initial_value='gap')


class ConstraintFunction(ConstraintExpression):

    def __init__(self, function_name: str = None):
        super().__init__(value=self)
        self.function_name = function_name
        self.parameters = []

    def __call__(self, *parameters):
        new_self = type(self)(self.function_name)
        new_self.parameters = parameters
        return new_self

    def __str__(self):
        return f'{self.function_name}({",".join(str(item) for item in self.parameters)})'

    def walk(self, function):
        raise RuntimeError('Should not walk in a function')

minimum = ConstraintFunction('min')
maximum = ConstraintFunction('max')


class ConstraintComposite(Constraint):

    def __init__(self, comparison: str = None):
        super().__init__()
        self.comparison = comparison

    def __call__(self, *parameters):
        new_self = type(self)(self.comparison)
        new_self.value = parameters
        return new_self

    def __str__(self):
        return ' '.join(f'{self.comparison}{str(item)}' for item in self.value)

    def serialize(self, target):
        return ';'.join(f'{target}{self.comparison}{str(item)}' for item in self.value)

at_least = ConstraintComposite('>')
at_most = ConstraintComposite('<')


class ConstraintAnchor(ConstraintExpression):

    def __init__(self, view=None, attribute=None):
        super().__init__()
        self.view = view
        self.attribute = attribute

    @property
    def value(self):
        js_attribute = Anchors.to_js.get(self.attribute, self.attribute)
        return f'{self.view.id}.{js_attribute}'

    @value.setter
    def value(self, ignored_value):
        pass


class ConstraintCondition(Constraint):

    def __init__(self, condition=None):
        super().__init__(condition)

    def __and__(self, other):
        constraint = Constraint(other)
        constraint.condition = self.value
        return constraint


class ConstraintConditionFixed(ConstraintCondition):
    """
    E.g.

        portrait?constraint - constraint applies if superview is tall
        landscape(root)?constraint - constraint applies if root view is wide
    """

    def __init__(self, keyword=None, view=None):
        if view:
            value = ConstraintExpression(initial_value=f'{keyword}({view.id})')
        else:
            value = ConstraintExpression(initial_value=keyword)
        super().__init__(value)

    def __call__(self, view):
        return ConstraintConditionFixed(self.value.initial_value, view)

portrait = ConstraintConditionFixed('portrait')
landscape = ConstraintConditionFixed('landscape')


class Anchors(BasicProperties):

    to_js = {
        'center_x': 'centerX',
        'center_y': 'centerY',
        'fit_height': 'fitHeight',
        'fit_width': 'fitWidth',
    }

    def __init__(self, gap=None, flow=False, **kwargs):
        self.flow = flow
        self._constraints = {}
        self._dock = None
        self._fit = False
        super().__init__(**kwargs)
        self.gap = gap
        
    gap = BasicProperties._prop('gap')
        
    def release(self):
        self._constraints = {}
        self._mark_dirty()

    def _is_fixed(self) -> bool:
        """
        Returns True if the position of the view is constrained, i.e. if any of left, top, right, bottom are used.
        """
        return bool(
            {'left', 'top', 'right', 'bottom', 'centerX', 'centerY'}.intersection(set(self._constraints.keys()))
        )
        
    @Render._register
    def _render_anchors(self):
        constraints_str = ';'.join(
            constraint.serialize(self.to_js.get(attribute, attribute))
            for attribute, constraints_by_comparison in self._constraints.items()
            for constraints in constraints_by_comparison.values()
            for constraint in constraints
        )

        #     if self._animation_id:
        #         attributes['ui4anim'] = self._animation_id
        #     return attributes
        # else:
        #     return {}

        return {'ui4': constraints_str}

    def _anchor_getter(self, attribute):
        return ConstraintAnchor(view=self, attribute=attribute)

    def _anchor_setter(self, attribute, value, comparison=None):
        self._mark_dirty()
        if value is None:
            self._constraints.pop(attribute, None)
            return

        if isinstance(value, Number):
            if attribute in ('right', 'bottom') and self.parent:
                value = getattr(self.parent, attribute) - value
            else:
                value = ConstraintExpression(value)
        if isinstance(value, Sequence):
            for item in value:
                setattr(self, attribute, item)
        elif isinstance(value, Constraint):
            value.animation = _animation_context()
            if value.condition:
                self._constraints.setdefault(attribute, {}).setdefault(value.comparison, []).append(value)
            else:
                self._constraints.setdefault(attribute, {})[value.comparison] = [value]

            # Adjust superview for containers
            source_anchor = value.get_anchor()
            if source_anchor and source_anchor.view == self.parent and self.parent != self._parent:
                source_anchor.view = self._parent

            # Release anchors where needed
            self._prune_anchors(attribute)

        else:
            raise TypeError(f"Cannot set {value} as {attribute}")

    def _anchor_process_sequence(self, attribute, anchors):
        for anchor in anchors:
            setattr(self, attribute, anchor)

    def _prune_anchors(self, attribute):
        """
        If caller has defined an impossible combination of constraints, select the most likely set.

        Only equal ('=') constraints are considered and pruned.
        """
        constrained_attributes = {
            attribute
            for attribute in self._constraints.keys()
            if '=' in self._constraints[attribute]
        }

        # Checklists define the priority order
        for checklist in (
            'width center_x left right'.split(),
            'height center_y top bottom'.split(),
        ):
            if attribute in checklist:
                per_dimension = constrained_attributes.intersection(set(checklist))
                if len(per_dimension) <= 2:
                    return  # All good
                per_dimension.discard(attribute)  # Latest attribute is kept
                for other_attribute in checklist:
                    if other_attribute in per_dimension:  # And another in list priority order
                        per_dimension.discard(other_attribute)
                        break
                for attribute_too_many in per_dimension:
                    del self._constraints[attribute_too_many]['=']
                    if not self._constraints[attribute_too_many]:
                        del self._constraints[attribute_too_many]

    @staticmethod
    def _anchorprop(attribute):
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
    def _anchordock(attribute):
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
    def _anchorprops(*attributes):
        return property(
            lambda self:
                partial(Anchors._anchor_multiple_getter, self, attributes)(),
            lambda self, value:
                partial(Anchors._anchor_multiple_setter, self, attributes, value)(),
        )
        
    @prop
    def fit(self, *value):
        if not value:
            return self._fit

        value = value[0]
        self._fit = value

        if value == True:
            value = 'both'

        extra_width = extra_height = 0

        if isinstance(value, Number):
            extra_width = extra_height = value
            value = 'both'

        if value not in ('width', 'height', 'both'):
            raise ValueError(f'Invalid value for fit: {self._fit}')
        if value in ('width', 'both'):
            self.width = self.fit_width + extra_width
        if value in ('height', 'both'):
            self.height = self.fit_height + extra_height

    @prop
    def dock(self, *value):
        if not value:
            return self._dock

        value = value[0]
        self._dock = value
        if isinstance(value, Sequence) and len(value) == 2:
            self.parent = value[0].view
            setattr(self, 'center', value)
            return
        if not isinstance(value, Constraint):
            raise TypeError(
                f'Dock value must be something like view.left, not {value}'
            )
        other_constraint = value.get_anchor()
        other = other_constraint.view
        dock_type = other_constraint.attribute
        dock_attributes = PARENT_DOCK_SPECS.get(dock_type)

        if dock_attributes:
            self.parent = other
            for attribute in dock_attributes:
                # other_constraint.attribute = attribute
                dock_constraint = copy.deepcopy(value)
                dock_constraint.get_anchor().attribute = attribute
                need_to_invert_sign = (
                    ANCHOR_TYPE[attribute] == TRAILING and
                    isinstance(dock_constraint, ConstraintExpression)
                )
                if need_to_invert_sign:
                    dock_constraint.invert_operator()
                setattr(self, attribute, dock_constraint)

        else:
            dock_attributes = SIBLING_DOCK_SPECS.get(dock_type)
            if dock_attributes:
                this, that, align, size = dock_attributes
                self.parent = other.parent
                #other_constraint.attribute = that
                dock_constraint = copy.deepcopy(value)
                dock_constraint.get_anchor().attribute = that
                if ANCHOR_TYPE[this] == TRAILING and isinstance(dock_constraint, ConstraintExpression):
                    dock_constraint.invert_operator()
                setattr(self, this, dock_constraint)  # edge
                setattr(self, align, getattr(other, align))  # center
                setattr(self, size, getattr(other, size))  # width or height
            else:
                raise ValueError(f'Unknown docking attribute {dock_type}')


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

NEUTRAL, LEADING, TRAILING = 'neutral', 'leading', 'trailing'

ANCHOR_TYPE = {
    'left': LEADING,
    'right': TRAILING,
    'top': LEADING,
    'bottom': TRAILING,
    'width': NEUTRAL,
    'height': NEUTRAL,
    'center_x': NEUTRAL,
    'center_y': NEUTRAL,
}


class CSSProperties(Anchors):
    """
    Logic for handling view properties.

    Property setters can mark the view as dirty, which means that the view
    (along with children) will be rendered when next update is sent to browser.
    """

    style = None
    _css_value_funcs = {}

    def __init__(self, **kwargs):
        self._css_properties = {}
        self._css_transitions = {}
        super().__init__(**kwargs)

    @Render._register
    def _render_props(self):
        css_properties = self._set_position_and_fill_from_theme()

        styles = ";".join(
            f"{name}:{value}"
            for name, value in css_properties.items()
            # if name not in self._css_transitions
        )

        attributes = {}

        if styles:
            attributes['style'] = styles

        if self._css_transitions:
            attributes['ui4style'] = ';'.join(self._css_transitions.values())
            self._css_transitions = {}
            # if self._animation_id:
            #     attributes['ui4anim'] = self._animation_id

        return attributes

    def _set_position_and_fill_from_theme(self):
        css_properties = dict(self._css_properties)

        if self._is_fixed():
            css_properties['position'] = 'absolute'

        if not self.style:
            return css_properties

        for key in dir(self.style):
            if key in css_properties or key.startswith('_'):
                continue
            css_spec = CSSProperties._css_value_funcs.get(key)
            if css_spec:
                css_name, css_value_func = css_spec
                value = getattr(self.style, key)
                if callable(value):
                    value = value(self.style)
                css_properties[css_name] = css_value_func(value)

        return css_properties

    def _set_css_property(
        self,
        property_name,
        property_value,
        css_name=None,
        css_value=None
    ):
        self._properties[property_name] = property_value
        if css_name:
            self._mark_dirty()
            animation = _animation_context()
            self._css_properties[css_name] = css_value
            if animation and animation.duration:
                transition = f'{css_name}:{css_value}:{animation.render()}'
                self._css_transitions[css_name] = transition

    def _css_setter(self, property_name, css_name, value, css_value_func):
        css_value = css_value_func(value)
        self._set_css_property(property_name, value, css_name, css_value)

    @staticmethod
    def _css_func_prop(css_value_func, property_name, css_name):
        CSSProperties._css_value_funcs[property_name] = css_name, css_value_func
        return property(
            lambda self: partial(
                CSSProperties._getter, self, property_name,
            )(),
            lambda self, value: partial(
                CSSProperties._css_setter,
                self, property_name,
                css_name,
                value,
                css_value_func,
            )()
        )

    @staticmethod
    def _css_plain_prop(property_name, css_name):
        def css_value_func(value):
            css_value = value
            if type(css_value) in (int, float):
                css_value = f'{css_value}px'
            elif isinstance(css_value, (tuple, list)):
                css_value = ','.join(css_value)
            return css_value

        return CSSProperties._css_func_prop(css_value_func, property_name, css_name)

    @staticmethod
    def _css_bool_prop(property_name, css_name, css_true_value):
        def css_value_func(value):
            return value and css_true_value or None

        return CSSProperties._css_func_prop(css_value_func, property_name, css_name)

    @staticmethod
    def _css_mapping_prop(property_name, css_name, css_value_mapping):
        def css_value_func(value):
            return css_value_mapping.get(value)

        return CSSProperties._css_func_prop(css_value_func, property_name, css_name)

    def _css_color_setter(self, property_name: str, css_name: str, value: ..., css_value_func: callable):
        if type(value) is not Color:
            value = Color(value)
        css_value = css_value_func(value)
        self._set_css_property(property_name, value, css_name, css_value)

    @staticmethod
    def _css_color_prop(property_name: str, css_name: str) -> property:
        def css_value_func(value):
            return value.css

        CSSProperties._css_value_funcs[property_name] = css_name, css_value_func
        return property(
            lambda self: partial(
                CSSProperties._getter, self, property_name,
            )(),
            lambda self, value: partial(
                CSSProperties._css_color_setter,
                self,
                property_name,
                css_name,
                value,
                css_value_func,
            )()
        )

    @staticmethod
    def _passthrough(inner_view_attribute_name: str, property_name: str) -> property:
        """
        For properties to be transparently passed through and from an enclosed view.

        Setting a passthrough property also marks the enclosing view as needing an update.
        """

        def setter(self, value):
            self._mark_dirty()
            setattr(getattr(self, inner_view_attribute_name), property_name, value)

        return property(
            lambda self: getattr(getattr(self, inner_view_attribute_name), property_name),
            setter,
        )


class Core(CSSProperties):
    """
    This class is here simply to collect the different mechanical parts of the core view class for inheritance.
    """
    @staticmethod
    def _clean_state():
        Identity._id_counter = defaultdict(int)
        Identity._views = defaultdict(dict)
        Events._dirties = dict()
        Events._animation_generators = dict()
        # CSSProperties._css_value_funcs = {}
