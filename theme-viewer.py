import ui4


def main(root):
    
    root.background_color = 'grey'
    
    holder = ui4.View(
        dock=root.center,
        width=ui4.minimum(root.width, root.height),
    )
    holder.height = holder.width
    
    button = ui4.Button(
        dock=holder.bottom,
        text='Move',
    )
    
    card = ui4.View(
        dock=holder.top,
        bottom=button.top,
        background_color='white',
    )
    
    ball = ui4.View(
        dock=card.bottom_left,
        size=(50, 50),
        corner_radius='50%',
        background_color='green',
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

ui4.run(main, port=8088)

