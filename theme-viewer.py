from ui4 import TextField
from ui4 import View
from ui4.app import run


def setup(root):
    textfield = TextField(placeholder='Enter color', dock=root.center, width=150)
    color_display = View(dock=textfield.below, height=textfield.height)

    @textfield
    def on_change(view):
        color_display.background_color = textfield.value

run(setup)
