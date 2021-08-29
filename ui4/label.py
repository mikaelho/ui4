from ui4.view import View
from ui4.prop import prop


class Label(View):

    DEFAULT_ALIGNMENT = {'center', 'middle'}
    DIMENSIONS = [
        {'left', 'center', 'right'},
        {'top', 'middle', 'bottom'},
    ]
    DOCK_KEYS = {
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
        self._text_view = View(parent=self)
        self._alignment = self.DEFAULT_ALIGNMENT
        self.alignment = alignment or set(self.DEFAULT_ALIGNMENT)
        self.apply(kwargs)

    @prop
    def alignment(self, *values):
        if not values:
            return self._alignment

        dock_key = self._get_dock_key(*values)
        self._text_view.release()
        self._text_view.dock = getattr(self, dock_key)

    def _get_dock_key(self, *values):
        values = values[0]
        self._alignment = self.DEFAULT_ALIGNMENT
        if not isinstance(values, (list, tuple, set)):
            values = {values}
        lookup_value = self._combine_keys(values)
        return self.DOCK_KEYS[lookup_value]

    def _combine_keys(self, values):
        for key in values:
            for dimension in self.DIMENSIONS:
                if key in dimension:
                    self._alignment = self._alignment.difference(dimension)
                    self._alignment.add(key)
                    break
            else:
                raise ValueError('Unknown label alignment value', key)
        return frozenset(self._alignment)