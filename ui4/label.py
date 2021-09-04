from ui4 import at_most
from ui4 import gap
from ui4.core import Constraint
from ui4.prop import prop
from ui4.theme import BaseStyle
from ui4.view import View


class Label(View):

    DEFAULT_ALIGNMENT = {'center', 'middle'}

    _DIMENSIONS = [
        {'left', 'center', 'right'},
        {'top', 'middle', 'bottom'},
    ]
    _DOCK_KEYS = {
        frozenset(('center', 'middle')): 'center',
        frozenset(('left', 'middle')): 'left_center',
        frozenset(('right', 'middle')): 'right_center',
        frozenset(('center', 'top')): 'top_center',
        frozenset(('left', 'top')): 'top_left',
        frozenset(('right', 'top')): 'top_right',
        frozenset(('center', 'bottom')): 'bottom_center',
        frozenset(('left', 'bottom')): 'bottom_left',
        frozenset(('right', 'bottom')): 'bottom_right',
    }

    def __init__(self, alignment=None, **kwargs):
        super().__init__(self)
        self._text_view = View(
            parent=self,
            style=BaseStyle,
        )
        self._alignment = self.DEFAULT_ALIGNMENT
        self.alignment = alignment or set(self.DEFAULT_ALIGNMENT)
        self.padding = 8
        self.apply(kwargs)

    font = View._passthrough('_text_view', 'font')
    font_size = View._passthrough('_text_view', 'font_size')
    text = View._passthrough('_text_view', 'text')

    @prop
    def alignment(self, *values):
        if not values:
            return self._alignment

        dock_key = self._get_dock_key(*values)
        self._text_view.release()
        self._text_view.dock = getattr(self, dock_key)
        # self._text_view.width = at_most(self.width - gap * 2)
        # self._text_view.height = at_most(self.height - gap * 2)

    @prop
    def width(self, *values):
        """
        Pass-through width property to constrain the inner view only when needed.
        """
        if not values:
            return View.width.fget(self)

        value = values[0]
        View.width.fset(self, value)
        if value is None:
            self._text_view.width = None
        elif not (isinstance(value, Constraint) and value.comparison != '='):
            self._text_view.width = at_most(self.width - gap * 2)

    @prop
    def height(self, *values):
        """
        Pass-through width property to constrain the inner view only when needed.
        """
        if not values:
            return View.height.fget(self)

        View.height.fset(self, values[0])
        if values[0] is not None:
            self._text_view.height = at_most(self.height - gap * 2)
        else:
            self._text_view.height = None

    def _get_dock_key(self, *values):
        values = values[0]
        self._alignment = self.DEFAULT_ALIGNMENT
        if not isinstance(values, (list, tuple, set)):
            values = {values}
        lookup_value = self._combine_keys(values)
        return self._DOCK_KEYS[frozenset(lookup_value)]

    def _combine_keys(self, values):
        for key in values:
            for dimension in self._DIMENSIONS:
                if key in dimension:
                    self._alignment = self._alignment.difference(dimension)
                    self._alignment.add(key)
                    break
            else:
                raise ValueError('Unknown label alignment value', key)
        return self._alignment

    alignment_horizontal = View._css_plain_prop('alignment_horizontal', 'justify-items')
    alignment_vertical = View._css_plain_prop('alignment_vertical', 'align-items')