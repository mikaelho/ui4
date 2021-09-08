from ui4 import TextField
from ui4 import View
from ui4.app import run


def setup(root):
    rootlike = View(dock=root.center, width=600, height=400)

    textfield = TextField(placeholder='Enter text', dock=rootlike.center)

    @textfield
    @delay(0.7)
    def on_change(value):
        print('Bling')

run(setup)

