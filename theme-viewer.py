import ui4


def main(root):
    
    root.background_color = 'grey'
    
    card = ui4.Card(
        title='Theme Viewer',
        background_color='white',
        dock=root.center,
        left=ui4.portrait(root.left),
        top=ui4.landscape(root.top),
    )
    card.height=ui4.portrait(card.width)
    card.width=ui4.landscape(card.height)
    #card.height = card.width
    
    button = ui4.Button(
        dock=card.bottom,
        text='Move',
    )
    
    play_area = ui4.View(
        dock=card.top,
        bottom=button.top,
    )
    
    ball = ui4.View(
        dock=play_area.bottom_left,
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
            setattr(ball, horizontal, getattr(play_area, horizontal))
        with ui4.animation(
            duration=0.5, ease='ease-in-out', 
            direction=ui4.ALTERNATE, iterations=3
        ):
            setattr(ball, vertical, getattr(play_area, vertical))
            ball.background_color = color

ui4.run(main, port=8088)

