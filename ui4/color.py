#coding: utf-8
from ui4.lib.webcolor import *


def prop(func):
    return property(func, func)


class Color(list):
    def __init__(self, *args, alpha=None):
        value = False
        if len(args) == 0:
            value = [0, 0, 0, 0]
        elif len(args) == 1:
            arg = args[0]
            if type(arg) is Color:
                value = arg.copy()
            elif type(arg) in (int, float):
                value = (arg, ) * 3
            elif type(arg) in (tuple, list):
                value = list(args[0])
            elif type(arg) is str:
                if arg == 'transparent':
                    value = [0, 0, 0, 0]
                elif arg.startswith('rgb'):
                    segments = arg[:-1].split('(')
                    value = [float(c) for c in segments[1].split(',')]
                else:
                    rgb = html5_parse_legacy_color(arg)
                    value = [rgb.red, rgb.green, rgb.blue]
        elif len(args) in [3, 4]:
            value = args
        if len(value) == 3:
            value = list(value)
            if alpha:
                value.append(alpha)
            elif not all((component <= 1.0) for component in value):
                value.append(255)
            else:
                value.append(1.0)
        elif len(value) == 4:
            value = list(value)
        elif alpha is not None:
            value[3] = alpha
        if not all((component <= 1.0) for component in value):
            for i in range(len(value)):
                value[i] /= 255.0
        super().__init__(value)

    def __eq__(self, other):
        if type(other) is tuple:
            other = list(other)
        return super().__eq__(other)

    @prop
    def r(self, *args):
        if args:
            self[0] = args[0]
        else:
            return self[0]

    @prop
    def g(self, *args):
        if args:
            self[1] = args[0]
        else:
            return self[1]

    @prop
    def b(self, *args):
        if args:
            self[2] = args[0]
        else:
            return self[2]

    @prop
    def a(self, *args):
        if args:
            self[3] = args[0]
        else:
            return self[3]

    red = r
    green = g
    blue = b
    alpha = a

    @prop
    def ints(self, *args):
        if args:
            self.css = args[0]
        else:
            return (int(self.r * 255), int(self.g * 255), int(self.b * 255), int(self.a * 255))

    @prop
    def css(self, *args):
        if args:
            c = Color(args[0])
            self.r = c.r
            self.g = c.g
            self.b = c.b
            self.a = c.a
        else:
            return f'rgba({",".join([str(segment) for segment in self.ints])})'

    @prop
    def name(self, *args):
        if args:
            self.css = args[0]
        else:
            try:
                value = rgb_to_name(tuple(self.ints[:3]))
            except ValueError:
                value = None
            return value

    @prop
    def hex(self, *args):
        if args:
            self.css = args[0]
        else:
            try:
                value = rgb_to_hex(tuple(self.ints[:3]))
            except ValueError:
                value = None
            return value

    @prop
    def transparent(self, *args):
        if args:
            self.alpha = 0.0 if args[0] else 1.0
        else:
            return self.alpha == 0

    def contrast_color(self,
                       low_brightness_color='black',
                       high_brightness_color='white'):
        r, g, b, a = self
        return Color(low_brightness_color) if (
            (r * 255 * 299 + g * 255 * 587 + b * 255 * 114) /
            1000) > 150 else Color(high_brightness_color)


def parse(cls, *args, alpha=None):
    return Color(*args, alpha=None)


def to_css_color(color, alpha=None):
    if type(color) is Color:
        return color.css
    if type(color) is str:
        return color
    if type(color) == tuple and len(color) >= 3:
        if alpha is None:
            alpha = color[3] if len(color) == 4 else 1.0
        if all((component <= 1.0) for component in color):
            color_rgb = [int(component * 255) for component in color[:3]]
            color_rgb.append(color[3] if len(color) == 4 else 1.0)
            color = tuple(color_rgb)
        return f'rgba{str(color)}'


def from_css_color(css_color_str):
    segments = css_color_str[:-1].split('(')
    components = [float(c) for c in segments[1].split(',')]
    if len(components) == 3:
        components.append(1.0)
    return components

