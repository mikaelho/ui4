import time

from ui4 import View
from ui4.app import run


def main(root):
    top_view = View(dock=root.top + 0)
    below_view = View(dock=top_view.below + 4)

    for view in (top_view, below_view):
        view.background_color = 'darkseagreen'
        view.height = 100

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

run(main)

