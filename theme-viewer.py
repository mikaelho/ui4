import ui4


demo_ui = ui4.GridContainer(
    dock=ui4.app.all,
    #fit='height',
    background_color='#d3ffd3',
)

ui4.GridView(
    parent=demo_ui,
    width=200,
    text=f"Something specific",
    background_color='lightgrey',
)

ui4.GridView(
    parent=demo_ui,
    width=200,
    text=f"TextField",
    background_color='lightgrey',
)

ui4.app.background_color = 'grey'

ui4.app.run()

