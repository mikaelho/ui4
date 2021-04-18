import ui4


def main(root):
    
    root.background_color = 'grey'
    
    card = ui4.View(
        dock=root.center,
        width=(
            ui4.high(root.width * 0.9),
            ui4.wide(root.height * 0.9),
        ),
        background_color='white',
    )
    card.height = card.width
    
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
        go_to('top', 'right', 'blue')
        yield
        go_to('bottom', 'left', 'green')
            
    def go_to(vertical, horizontal, color):
        with ui4.duration(1.5):
            setattr(ball, horizontal, getattr(card, horizontal))
        with ui4.animation(
            duration=0.5, ease='ease-in-out', 
            direction=ui4.ALTERNATE, iterations=3
        ):
            setattr(ball, vertical, getattr(card, vertical))
            ball.background_color = color

ui4.run(main)

