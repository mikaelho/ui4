from ui4.theme import ButtonStyle
from ui4.view import View


class Button(View):
    _tag = 'button'
    style = ButtonStyle

    def __init__(self, padding=8, **kwargs):
        super().__init__()
        self.padding = padding
        self.apply(kwargs)