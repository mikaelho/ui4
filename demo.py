import ui4

v = ui4.View(
    parent=ui4.app,
    x=None, y=None, right=25, bottom=25, width=300, height=300,
    background_color='red',
)

btn = ui4.Button(
    parent=v, x=None, right=25,
    background_color='blue',
)


ui4.run()

