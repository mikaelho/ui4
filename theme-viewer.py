from ui4 import *


demo_ui = GridContainer(
    dock=app.all,
    #fit='height',
    background_color='#d3ffd3',
)

GridView(
    parent=demo_ui,
    width=200,
    text=f"Something specific",
    background_color='lightgrey',
)

GridView(
    parent=demo_ui,
    width=200,
    text=f"TextField",
    background_color='lightgrey',
)

app.background_color = 'grey'

app.run()

