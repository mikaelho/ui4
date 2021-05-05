from string import Template

from ui4.core import Core
from ui4.theme import TextInputStyle
from ui4.view import View


class TextField(View):
    
    NORMAL = 'text'
    PASSWORD = 'password'
    EMAIL = 'email'
    URL = 'url'
    PHONE = 'tel'
    SEARCH = 'search'
    
    _template = Template(
        '<input id="$id" name="$id" class="$viewclass" '
        '$rendered_attributes '
        '$oob hx-swap="none" '
        'value="$content"></input>'
    )
    style = TextInputStyle
    
    def __init__(self, type=NORMAL, placeholder="", **kwargs):
        super().__init__(**kwargs)
        self._css_properties['user-select'] = 'auto'
        self.type = type
        self.placeholder = placeholder

    type = Core._prop('type')
    placeholder = Core._prop('placeholder')
    value = Core._prop('value')
    
    def on_change(self, value):
        self._properties['text'] = value
    
    def _additional_attributes(self):
        add = super()._additional_attributes()
        add.update({
            'type': self.type,
            'placeholder': self.placeholder,
        })
        return add

