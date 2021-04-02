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
        with ui4.animation(0.5):
            view.text_color = 'white'
            view.background_color = 'red'
            button.top = view.bottom + 100
            yield 0.5
            button.top = view.bottom


ui4.run(main)

