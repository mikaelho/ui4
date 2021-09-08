from string import Template

from ui4.theme import ButtonStyle
from ui4.view import View


class Button(View):
    
    _template = Template(
        '<button type="button" id="$id" class="$viewclass" '
        '$rendered_attributes $oob hx-swap="none">$content</button>'
    )
    style = ButtonStyle

    def __init__(self, padding=8, **kwargs):
        super().__init__(self)
        self.padding = padding
        self.apply(kwargs)