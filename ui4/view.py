# Base view class

from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from string import Template
from types import GeneratorType

import ui4.constants as constants

from ui4.prop import css, cssprop_color, cssprop_onoff, cssprop_px_or_str
from ui4.prop import prop, ui4prop, ui4props, ui4dock, Anchor

from ui4.core import Core


class View(Core):
    
    # Layout properties
    left = Core.anchorprop('left')
    x = left
    right = Core.anchorprop('right')
    top = Core.anchorprop('top')
    y = top
    bottom = Core.anchorprop('bottom')
    width = Core.anchorprop('width')
    height = Core.anchorprop('height')
    center_x = Core.anchorprop('centerX')
    center_y = Core.anchorprop('centerY')
    
    # Composite properties
    center = Core.anchorprops('center_x', 'center_y')
    position = Core.anchorprops('left', 'top')
    size = Core.anchorprops('width', 'height')
    box = Core.anchorprops('left', 'top', 'width', 'height')
    
    # Dock to parent
    top_left = Core.anchordock('top_left')
    top_right = Core.anchordock('top_right')
    bottom_left = Core.anchordock('bottom_left')
    bottom_right = Core.anchordock('bottom_right')
    top_center = Core.anchordock('top_center')
    bottom_center = Core.anchordock('bottom_center')
    left_center = Core.anchordock('left_center')
    right_center = Core.anchordock('right_center')
    sides = Core.anchordock('sides')
    top_and_bottom = Core.anchordock('top_and_bottom')
    all = Core.anchordock('all')
    
    # Dock to sibling
    above = Core.anchordock('above')
    below = Core.anchordock('below')
    left_of = Core.anchordock('left_of')
    right_of = Core.anchordock('right_of')
    
    # Appearance properties
    align = Core._css_plain_prop('align', 'text-align')
    background_color = Core._css_color_prop('background_color', 'background-color')
    bold = Core._css_bool_prop('bold', 'font-weight', 'bold')
    border_color = Core._css_color_prop('border_color', 'border-color')
    border_style = Core._css_plain_prop('border_style', 'border-style')
    border_width = Core._css_plain_prop('border_width', 'border-width')
    corner_radius = Core._css_plain_prop('corner_radius', 'border-radius')
    alpha = Core._css_plain_prop('alpha', 'opacity')
    padding = Core._css_plain_prop('padding', 'padding')
    shadow = Core._css_plain_prop('shadow', 'box-shadow')
    text_color = Core._css_color_prop('text_color', 'color')
    z = Core._css_plain_prop('z', 'z-index')
