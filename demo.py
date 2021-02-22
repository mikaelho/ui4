import random

from ui4 import *


card = View(
    dock=app.center,
    fit=True,
    background_color='white',
    corner_radius=8,
    text_color='grey',
    shadow=(2, 2, 8),
)

title = View(
    dock=card.top_center,
    width=200,
    text="Welcome, Captain",
    text_color='black',
    bold=True,
)

email = TextField(
    dock=title.below,
    type=TextField.EMAIL,
    placeholder="Enter email",
)

password = TextField(
    dock=email.below,
    type=TextField.PASSWORD,
    placeholder="Enter password",
)

error = View(
    dock=password.below,
    text="Please try again",
    text_color='red',
    alpha=0,
)

submit = View(
    dock=password.below,
    text="Login",
    background_color='#28184e',
    text_color='white',
)

@submit
def on_click(data):
    submit.top = error.bottom
    error.alpha = 1
    submit.animated = True
    
    #after(2, fade)


app.background_color = 'lightgrey'

run()

