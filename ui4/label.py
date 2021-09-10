from ui4 import at_most
from ui4 import gap
from ui4.core import Constraint
from ui4.prop import prop
from ui4.theme import BaseStyle
from ui4.view import View


class Label(View):

    _DIMENSIONS = {
        'alignment_horizontal': {'left', 'center', 'right'},
        'alignment_vertical': {'top', 'middle', 'bottom'},
    }
    DEFAULT_ALIGNMENT = {'center', 'middle'}

    def __init__(self, alignment=None, padding=8, **kwargs):
        super().__init__(self)
        self._text_view = View(
            parent=self,
            style=BaseStyle,
            _css_class='label-content',
        )
        # self._text_view._mark_dirty = lambda: self._mark_dirty()
        self._css_class = 'label'
        self._alignment = self.DEFAULT_ALIGNMENT
        self.alignment = alignment or set(self.DEFAULT_ALIGNMENT)
        self.padding = padding
        self.apply(kwargs)

    font = View._passthrough('_text_view', 'font')
    font_size = View._passthrough('_text_view', 'font_size')
    text = View._passthrough('_text_view', 'text')
    text_style = View._passthrough('_text_view', 'style')

    @prop
    def alignment(self, *values):
        if not values:
            return self._alignment

        value = values[0]
        if not isinstance(value, (list, tuple, set)):
            value = {value}
        self._combine_keys(value)
        for dimension_key, keywords in self._DIMENSIONS.items():
            for key in keywords:
                if key in self._alignment:
                    setattr(self, dimension_key, key)

    def _combine_keys(self, values):
        for key in values:
            for dimension in self._DIMENSIONS.values():
                if key in dimension:
                    self._alignment = self._alignment.difference(dimension)
                    self._alignment.add(key)
                    break
            else:
                raise ValueError('Unknown label alignment value', key)
        return self._alignment

    alignment_horizontal = View._css_mapping_prop('alignment_horizontal', 'align-items', {
        'left': 'flex-start',
        'center': 'center',
        'right': 'flex-end',
    })
    alignment_vertical = View._css_mapping_prop('alignment_vertical', 'justify-content', {
        'top': 'flex-start',
        'middle': 'center',
        'bottom': 'flex-end',
    })
