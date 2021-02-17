# Base view class
import copy

from pathlib import Path
from string import Template

import ui4.constants as constants

from ui4.prop import cssprop_color, cssprop_px_or_str
from ui4.prop import prop, ui4prop, ui4props, ui4dock, Anchor


class View:
    
    # Keep to one class only not to get into a CSS mess
    _css_class = 'view'
    
    def __init__(
        self,
        parent=None,
        children=None,
        **kwargs
    ):
        self.id = View._get_id()
        self._parent = None
        self.parent = parent
        self.children = children or list()
        self._dirty = False
        
        self._values = {}
        self._style_values = {}
        self._constraints = {}
        self._dock = None
        
        self.text = None
    
        for key in kwargs:
            setattr(self, key, kwargs[key])
                
    @classmethod
    def _get_id(cls):
        if not hasattr(cls, '_id_counter'):
            cls._id_counter = 1
        else:
            cls._id_counter += 1
        return f'ui4{cls._id_counter}'
        
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
    background_color = cssprop_color('background_color', 'background-color')
    border_radius = cssprop_px_or_str('border_radius', 'border-radius')
    padding = cssprop_px_or_str('padding', 'padding')
    shadow = cssprop_px_or_str('shadow', 'box-shadow')
    text_color = cssprop_color('text_color', 'color')
    
    @prop
    def fit(self, value=prop.none):
        if value == prop.none:
            return self._fit
        else:
            self._fit = value
            if value not in ('width', 'height', True):
                raise ValueError(f'Invalid value for fit: {value}')
            if value in ('width', True):
                setattr(self, 'width', Anchor(view=self, attribute='fitWidth'))
            if value in ('height', True):
                setattr(self, 'height', Anchor(view=self, attribute='fitHeight'))
    
    @prop
    def dock(self, value=prop.none):
        if value == prop.none:
            return self._dock
        else:
            self._dock = value
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
                
    def __call__(self, f):
        """
        Enable using instances of this class as event-handler decorators.
        """
        if f.__name__ in ['clicked']:
            setattr(self, f.__name__, f)
        return f
        
    def _process_event(self, event_name, event_data=None):
        if hasattr(self, event_name):
            getattr(self, event_name)(event_data)
                
    def _render(self):
        
        constraints = self._render_constraints()
        styles = self._render_styles()
        child_content = ''.join([
            child._render()
            for child in self.children
        ])
        
        template = Template(Path('ui4/static/view_template.html').read_text())
        
        html = template.safe_substitute(
            id=self.id,
            viewclass = self._css_class,
            constraints=constraints,
            styles=styles,
            content=child_content or self.text
        )
        
        print(html)
        
        return html
        
    def _render_constraints(self):
        print(self._constraints)
        constraints = []
        for attribute in self._constraints:
            constraints.append(" ".join([
                f"{attribute}{str(constraint)}"
                for constraint
                in self._constraints[attribute]
            ]))
        return " ".join(constraints)
                
    def _render_styles(self):
        return " ".join([
            f"{key}: {value};"
            for key, value
            in self._style_values.items()
        ])

