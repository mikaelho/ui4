from string import Template

from ui4.core import Render
from ui4.theme import TextInputStyle
from ui4.view import prop
from ui4.view import View


class TextField(View):
    
    NORMAL = 'text'
    PASSWORD = 'password'
    EMAIL = 'email'
    URL = 'url'
    PHONE = 'tel'
    
    _template = Template(
        '<input id="$id" name="$id" class="$viewclass" '
        '$rendered_attributes '
        '$oob hx-swap="none" '
        'value="$content"></input>'
    )
    style = TextInputStyle
    
    def __init__(self, type=NORMAL, placeholder="", **kwargs):
        self.type = type
        self.placeholder = placeholder
        super().__init__(**kwargs)
        self._css_properties['user-select'] = 'auto'
        self.align = 'left'
        self._value = ""

    @prop
    def type(self, value=prop.none):
        if value == prop.none:
            return self._type
        else:
            self._type = value
            self._mark_dirty()
            
    @prop
    def placeholder(self, value=prop.none):
        if value == prop.none:
            return self._placeholder
        else:
            self._placeholder = value
            self._mark_dirty()
            
    @prop
    def value(self, value=prop.none):
        if value == prop.none:
            return self._value
        else:
            self._value = value
            self._mark_dirty()
    
    def on_change(self, value):
        self._value = value
    
    def _additional_attributes(self):
        add = super()._additional_attributes()
        add.update({
            'type': self._type,
            'placeholder': self._placeholder,
        })
        return add

