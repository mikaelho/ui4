import ui4


def main(root):
    view = ui4.View(
        dock=root.center,
        text='Hello world',
    )
    button = ui4.Button(
        dock=view.below,
        text='Button',
    )
    
    @button
    def on_click(data):
        view.center_y.clear()
        with ui4.animation(0.5):
            view.text_color = 'white'
            view.background_color = 'red'
            view.top = view.parent.top


ui4.run(main)

