from ui4 import *

holder = View(
    parent=app,
    center=app.center,
    background_color='white',
    border_radius=8,
    fit=True,
    text_color='black',
    shadow=(0, 0, 6, 2),
)


v = View(
#    width=(app.width * 0.9, gt(btn.width)),
    dock=holder.top,
    text="Foobar",
    background_color='#4e4e4e',
    text_color='white',
    border_radius=8,
# Overwrite existing absolute constraint
)

v2 = View(
    dock=v.below,
    text="Other",
    background_color='#28184e',
    text_color='white',
    border_radius=8,
)


#btn = Button(
#    dock=top(v),
#    background_color='blue',
#    text_color='white',
#)

app.background_color = '#eafbd3'

run()

