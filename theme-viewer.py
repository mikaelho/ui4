import time

from ui4 import Label
from ui4 import View
from ui4 import at_most
from ui4.app import run


def setup(root):
    rootlike = View(dock=root.center, width=600, height=400)

    # Baseline fitted label
    label1 = Label(text='Label with text', dock=rootlike.center, background_color='darkseagreen')

    # Limiting one dimension flexes the other if needed
    label1b = Label(text='Label with text', dock=rootlike.right_center, background_color='darkseagreen')
    label1b.width = at_most(80)

    # Docking requires releasing the fit
    label2 = Label(text='Label with text', dock=rootlike.top, background_color='darkseagreen')

    # Fixing one dimension flexes the other - width locked
    label3 = Label(
        text='A little more text to make things interesting',
        background_color='darkseagreen',
        dock=rootlike.bottom_center,
        width=150,
    )

    # Fixing one dimension flexes the other - height locked
    label4 = Label(
        text='A little more text to fit',
        background_color='darkseagreen',
        dock=rootlike.left_center,
        height=50,
    )

    # Fixing both dimensions truncates the text if needed
    label_not_numbered__how_to_test_questionmark = Label(
        text='Just too much text that gets neatly cut at the end, or does it? Well, of course not.',
        background_color='darkseagreen',
        dock=rootlike.bottom_right,
        width=150,
        height=50,
    )

    # Different text alignment
    label5 = Label(
        text='Top right corner',
        alignment=('top', 'right'),
        background_color='darkseagreen',
        dock=rootlike.bottom_left,
        width=150,
        height=150,
    )
    print(label5._render_props())

    # for view in (top_view, below_view):
    #     view.background_color = 'darkseagreen'
    #     view.height = 100

    # root.background_color = 'grey'
    #
    # card = ui4.Card(
    #     title='Theme Viewer',
    #     background_color='white',
    #     dock=root.center,
    # )

    # card.height.minimum(root.width, root.height)
    # card.width = card.height - 16
    #
    # button = ui4.Button(
    #     dock=card.bottom,
    #     text='Move',
    # )
    #
    # play_area = ui4.View(
    #     dock=card.top,
    #     bottom=button.top,
    # )

    # ball = ui4.View(
    #     dock=play_area.bottom_left,
    #     size=(50, 50),
    #     corner_radius='50%',
    #     background_color='green',
    # )
    #
    # @button
    # def on_click(data):
    #     go_to('top', 'right', 'blue')
    #     yield
    #     go_to('bottom', 'left', 'green')
    #
    # def go_to(vertical, horizontal, color):
    #     with ui4.duration(1.5):
    #         setattr(ball, horizontal, getattr(play_area, horizontal))
    #     with ui4.animation(
    #         duration=0.5, ease='ease-in-out',
    #         direction=ui4.ALTERNATE, iterations=3
    #     ):
    #         setattr(ball, vertical, getattr(play_area, vertical))
    #         ball.background_color = color

run(setup)

