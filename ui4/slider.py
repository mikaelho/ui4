from string import Template

from ui4 import ButtonStyle
from ui4 import View


class Slider(View):
    _tag = 'input'
    style = ButtonStyle

    def __init__(self, min_value=0, max_value=1, **kwargs):
        super().__init__(self)
        self.min_value = min_value
        self.max_value = max_value
        self.apply(kwargs)

    value = View._prop('value')
    min_value = View._prop('min_value')
    max_value = View._prop('max_value')

    def _additional_attributes(self):
        attributes = super()._additional_attributes()
        attributes.update({
            'type': 'range',
            'step': 'any',
            'min': self.min_value,
            'max': self.max_value,
            'value': self.value or '',
        })
        return attributes
