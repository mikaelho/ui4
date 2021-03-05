"""
Contains behind-the-scenes machinery that all views share.
"""

from types import GeneratorType
from weakref import WeakValueDictionary


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
    """

    def __init__(self, parent=None, children=None, **kwargs):
        super().__init__(**kwargs)
        self._parent = None
        self._children = list()
        self.parent = parent

        children = children or []
        for child in children:
            child.parent = self

    @prop
    def parent(self, *value):
        if value:
            if self._parent:
                self._parent._children.remove(self)  # noqa
            self._parent = value[0]
            if self._parent and self not in self._parent._children:
                self._parent._children.append(self)
        else:
            return self._parent

    @property
    def children(self):
        return tuple(self._children)


class Render(Hierarchy):
    """
    Renders a view, recursively rendering the child views first.
    """
    ...


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
    # "next" is special case, custom event that we use to trigger the next step in an event handler generator.
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
            raise ValueError(f'{f.__name__} is not an event handler name: {self._event_methods.keys()}')
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
        for dirty in self._dirties:
            parent = dirty.parent
            while parent:
                if parent in self._dirties:
                    continue
                parent = parent.parent
            roots.add(dirty)

        self._dirties.clear()

        return "".join([
            root._render(oob=True) for root in roots
        ])


class Core(Events):
    """
    This class is here simply to collect the different mechanical parts of the core view class for inheritance.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
