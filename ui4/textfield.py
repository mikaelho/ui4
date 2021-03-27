from ui4.theme import TextInputStyle
from ui4.view import prop
from ui4.view import View


class TextField(View):
    
    NORMAL = 'text'
    PASSWORD = 'password'
    EMAIL = 'email'
    URL = 'url'
    PHONE = 'tel'
    
    _render_template = 'textfield_template.html'
    _style = TextInputStyle
    
    def __init__(self, type=NORMAL, placeholder="", **kwargs):
        self.type = type
        self.placeholder = placeholder
        super().__init__(**kwargs)
        self._style_values['user-select'] = 'auto'
        self.align = 'left'
        self._value = ""

    @prop
    def type(self, value=prop.none):
        if value == prop.none:
            return self._type
        else:
            self._type = value
            View._dirties.add(self)
            
    @prop
    def placeholder(self, value=prop.none):
        if value == prop.none:
            return self._placeholder
        else:
            self._placeholder = value
            View._dirties.add(self)
            
    @prop
    def value(self, value=prop.none):
        if value == prop.none:
            return self._value
        else:
            self._value = value
            View._dirties.add(self)
    
    def on_change(self, value):
        self._value = value
    
    def _render__additional_values(self):
        return {
            'type': self._type,
            'placeholder': self._placeholder,
        }

