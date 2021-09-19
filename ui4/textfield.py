from string import Template

from ui4.core import Core
from ui4.theme import TextInputStyle
from ui4.view import View


class TextField(View):
    
    NORMAL = 'text'
    NUMBER = 'number'
    PASSWORD = 'password'
    EMAIL = 'email'
    URL = 'url'
    PHONE = 'tel'
    DATE = 'date'
    TIME = 'time'
    DATETIME = 'datetime-local'
    MONTH = 'month'
    WEEK = 'week'
    COLOR = 'color'

    _template = Template(
        '<input id="$id" name="$id" class="$viewclass" '
        '$rendered_attributes '
        '$oob hx-swap="none" '
        '></input>'
    )
    style = TextInputStyle
    
    def __init__(self, field_type=NORMAL, placeholder="", **kwargs):
        super().__init__(**kwargs)
        self._css_properties['user-select'] = 'auto'
        self.field_type = field_type
        self.placeholder = placeholder
        self.padding = 4

    field_type = Core._prop('field_type')
    placeholder = Core._prop('placeholder')
    value = Core._prop('value')
    
    def on_change(self, value):
        self._properties['text'] = value
    
    def _additional_attributes(self):
        add = super()._additional_attributes()
        add.update({
            'type': self.field_type,
            'placeholder': self.placeholder,
            'value': self.value or '',
        })
        return add

