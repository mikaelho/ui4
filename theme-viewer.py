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
    other_button = ui4.Button(
        dock=button.below,
        text='Other button with long text',
        style=ui4.VariantButtonStyle,
    )
    textf = ui4.TextField(
        dock=view.above,
        placeholder="Some text?",
    )
    
    @button
    def on_click(data):
        view.center_y.clear()
        with ui4.animation(2.0):
            view.text_color = 'white'
            view.background_color = 'red'
            view.bottom = view.parent.top + 0


ui4.run(main)

