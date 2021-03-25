import ui4


def main(root):
    ui4.View2(
        dock=root.center,
        background_color='palegreen',
        text='Hello world',
    )

ui4.run(main)

