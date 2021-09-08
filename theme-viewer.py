from ui4 import Button
from ui4.app import run
from ui4.core import delay


def setup(root):
    button = Button(text='Click me', dock=root.center, width=150)
    button.counter = 0

    @button
    @delay(0.1)
    def on_load(view):
        print('CALLED')
        view.counter += 1
        view.text = f'Clicked {view.counter} time(s)'
        if view.counter == 2:
            view.remove_event('load')

    assert button._render_events() == {'hx-post': '/event', 'hx-trigger': 'load delay:0.1s'}

run(setup)

