# Base view class
import copy

from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from string import Template

import ui4.constants as constants

from ui4.prop import css, cssprop_color, cssprop_onoff, cssprop_px_or_str
from ui4.prop import prop, ui4prop, ui4props, ui4dock, Anchor


class View:
    
    gap = 8
    halfgap = gap/2
    
    # Keep to one class only not to get into a CSS mess
    _render_template = 'view_template.html'
    _css_class = 'view'
    _id_counter = 0
    _views = {}
    _dirties = set()
    _animated = False
    
    _event_methods = {        
        'on_click': 'click',
    }
    
    def __init__(
        self,
        parent=None,
        children=None,
        **kwargs
    ):
        self.id = View._get_id(self)
        self._parent = None
        self.parent = parent
        self.children = children or list()
        
        self._values = {}
        self._style_values = {}
        self._constraints = {
            '=': {},
            '>': {},
            '<': {},
        }
        self._dock = None
        self._z_min = _z_max = 0
        
        self.text = None
        #self._animated = False
        self._transitions = []
    
        for key in kwargs:
            setattr(self, key, kwargs[key])
                
    @classmethod
    def _get_id(cls, view):
        View._id_counter += 1
        view_id = f'id{cls._id_counter}'
        View._views[view_id] = view
        return view_id
        
    @property    
    def parent(self):
        return self._parent
        
    @parent.setter
    def parent(self, value):
        if self._parent:
            self._parent.children.remove(self)
        self._parent = value
        if self._parent and not self in self._parent.children:
            self._parent.children.append(self)
        
    # Layout properties
    left = ui4prop('left')
    x = ui4prop('left')
    right = ui4prop('right')
    top = ui4prop('top')
    y = ui4prop('top')
    bottom = ui4prop('bottom')
    width = ui4prop('width')
    height = ui4prop('height')
    center_x = ui4prop('centerX', False)
    center_y = ui4prop('centerY', False)
    
    # Composite properties
    center = ui4props('center_x', 'center_y')
    position = ui4props('left', 'top')
    size = ui4props('width', 'height')
    box = ui4props('left', 'top', 'width', 'height')
    
    # Dock to parent
    top_left = ui4dock('top_left')
    top_right = ui4dock('top_right')
    bottom_left = ui4dock('bottom_left')
    bottom_right = ui4dock('bottom_right')
    top_center = ui4dock('top_center')
    bottom_center = ui4dock('bottom_center')
    left_center = ui4dock('left_center')
    right_center = ui4dock('right_center')
    sides = ui4dock('sides')
    top_and_bottom = ui4dock('top_and_bottom')
    all = ui4dock('all')
    
    # Dock to sibling
    above = ui4dock('above')
    below = ui4dock('below')
    left_of = ui4dock('left_of')
    right_of = ui4dock('right_of')
    
    # Appearance properties
    align = css('align', 'text-align')
    background_color = cssprop_color('background_color', 'background-color')
    bold = cssprop_onoff('bold', 'font-weight', 'bold')
    corner_radius = cssprop_px_or_str('corner_radius', 'border-radius')
    alpha = css('alpha', 'opacity')
    padding = cssprop_px_or_str('padding', 'padding')
    shadow = cssprop_px_or_str('shadow', 'box-shadow')
    text_color = cssprop_color('text_color', 'color')
    z = css('z', 'z-index')
    
    @prop
    def fit(self, value=prop.none):
        if value == prop.none:
            return self._fit
        else:
            self._fit = value
            if type(value) in (int, float):
                extra_width = extra_height = value
                value = True
            else:
                extra_width = extra_height = 0
            if value not in ('width', 'height', True):
                raise ValueError(f'Invalid value for fit: {value}')
            if value in ('width', True):
                setattr(self, 'width', Anchor(
                    view=self, 
                    attribute='fitWidth',
                    operator='+',
                    constant=extra_width
                ))
            if value in ('height', True):
                setattr(self, 'height', Anchor(
                    view=self, 
                    attribute='fitHeight',
                    operator='+',
                    constant=extra_height
                ))
    
    @prop
    def dock(self, value=prop.none):
        if value == prop.none:
            return self._dock
        else:
            self._dock = value
            if issubclass(type(value), Sequence) and len(value) == 2:
                value = value[0]
                value.attribute = 'center'
            if not type(value) is Anchor:
                raise TypeError(f'Dock value must be an Anchor, not {value}')
            other = value.view
            dock_type = value.attribute
            if dock_type in constants.PARENT_DOCK_SPECS:
                self.parent = other
                for attribute in constants.PARENT_DOCK_SPECS[dock_type]:
                    setattr(self, attribute, getattr(other, attribute))
            else:
                self.parent = other.parent
                if dock_type == 'above':
                    self.center_x = other.center_x
                    self.bottom = other.top
                    self.width = other.width
                elif dock_type == 'below':
                    self.center_x = other.center_x
                    self.top = other.bottom
                    self.width = other.width
                elif dock_type == 'left_of':
                    self.center_y = other.center_y
                    self.right = other.left
                    self.height = other.height
                elif dock_type == 'right_of':
                    self.center_y = other.center_y
                    self.left = other.right
                    self.height = other.height
                else:
                    raise ValueError(f'Unknown docking type {dock_type}')
                
    def send_to_back(self):
        self.parent._z_min -= 1
        self.z = self.parent._z_min
        
    def bring_to_front(self):
        self.parent._z_max += 1
        self.parent._z_max = max(len(self.parent.children), self.parent._z_max)
        self.z = self.parent._z_max
                
    def __call__(self, f):
        """
        Enable using instances of this class as event-handler decorators.
        """
        if f.__name__ in self._event_methods.keys():
            setattr(self, f.__name__, f)
        return f
        
    def _process_event(self, event_name, event_data=None):
        event_method = getattr(self, f'on_{event_name}', None)
        event_method and event_method(event_data)
        return self._render_updates()
    
    @classmethod
    @contextmanager    
    def animated(cls):
        cls._animated = True
        yield 
        cls._animated = False
        
    def _render_updates(self):
        roots = set()
        
        # Determine roots of the subtrees that need refreshing
        for dirty in View._dirties:
            parent = dirty.parent
            while parent:
                if parent in View._dirties:
                    continue
                parent = parent.parent
            roots.add(dirty)
            
        View._dirties = set()
            
        return "".join([
            root._render(oob=True) for root in roots
        ])
                
    def _render(self, oob=''):        
        constraints = self._render__constraints()
        styles = self._render__styles()
        events = self._render__events()
        oob = oob and 'hx-swap-oob="true"'
        rendered_children = ''.join([
            child._render()
            for child in self.children
        ])
        
        template = Template(
            Path(f'ui4/static/{self._render_template}').read_text()
        )
        return self._render_result(constraints, styles, events, oob, rendered_children, template)
        
    def _render_result(self, constraints, styles, events, oob, rendered_children, template):
        additional_values = self._render__additional_values()
        
        html = template.safe_substitute(
            id=self.id,
            viewclass = self._css_class,
            constraints=constraints,
            events=events,
            oob=oob,
            styles=styles,
            content=rendered_children or self.text or "",
            **additional_values
        )
        
        return html
        
    def _render__additional_values(self):
        return {}
        
    def _render__constraints(self):
        constraints = []
        for comparison in self._constraints.values():
            for attribute in comparison:
                constraints.append(" ".join([
                    constraint.render(attribute)
                    for constraint
                    in comparison[attribute]
                ]))
        return " ".join(constraints)
        
    def _render__events(self):
        return " ".join([
            f"hx-get='/event' hx-vals='{{\"id\": \"{self.id}\"}}'"
            for method_name, event in self._event_methods.items()
            if hasattr(self, method_name)
        ])
                
    def _render__styles(self):
        styles = " ".join([
            f"{key}: {value};"
            for key, value
            in self._style_values.items()
        ])
        if self._transitions:
            styles += (
                f' transition-property: {",".join(self._transitions)}; '
                'transition-duration: 1.0s;'
            )
            self._transitions = []

        return styles

