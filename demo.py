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

submit = View(
    dock=password.below,
    text="Login",
    background_color='#28184e',
    text_color='white',
)

@submit
def on_click(data):
    with View.animated():
        if email.value == "aa" and password.value == "bb":
            submit.background_color = 'green'
        else:
            submit.background_color = 'red'


app.background_color = 'lightgrey'

run()

