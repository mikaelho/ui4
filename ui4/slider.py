from string import Template

from ui4 import ButtonStyle
from ui4 import View


class Slider(View):
    _template = Template(
        '<input type="range" id="$id" class="$viewclass" '
        '$rendered_attributes $oob hx-swap="none" step="any"></input>'
    )
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
        add = super()._additional_attributes()
        add.update({
            'min': self.min_value,
            'max': self.max_value,
            'value': self.value or '',
        })
        return add