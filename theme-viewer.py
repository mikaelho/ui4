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
        print('bling')
        with ui4.animation(1.0):
            view.center_x = root.right

ui4.run(main)

