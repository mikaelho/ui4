import ui4


def main(root):
    
    root.background_color = 'grey'
    
    card = ui4.View(
        dock=root.center,
        width=root.width * 0.9,
        height=root.width * 0.9,
        background_color='white',
    )
    
    ball = ui4.View(
        dock=card.bottom_left,
        size=(50, 50),
        corner_radius='50%',
        background_color='green',
    )
    
    button = ui4.Button(
        dock=card.below,
        text='Move',
    )
    
    @button
    def on_click(data):
        ball.left.clear()
        ball.bottom.clear()
        with ui4.duration(1.0):
            ball.right = card.right
            with ui4.ease('ease-in-out'):
                ball.top = card.top
                ball.background_color = 'blue'


ui4.run(main)

