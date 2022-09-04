from ui4 import Button
from ui4 import DefaultTheme
from ui4 import TextField
from ui4 import View
from ui4.app import run


def setup(root):
    root.background_color = DefaultTheme.tinted

    # center_area = View(background_color='white', dock=root.center, fit=True)

    left_column = View(
        border_width=1, border_color=DefaultTheme.primary, background_color='white',
        fit=True, parent=root, right=root.center_x, center_y=root.center_y,
    )
    right_column = View(
        border_width=1, border_color=DefaultTheme.primary, background_color='white',
        fit=True, parent=root, left=root.center_x, center_y=root.center_y, size=left_column.size,
    )

    field_text = TextField(placeholder='Text', dock=left_column.top_left, width=200)
    field_number = TextField(field_type=TextField.NUMBER, placeholder='Number', dock=field_text.below)
    field_email = TextField(field_type=TextField.EMAIL, placeholder='Email', dock=field_number.below)
    field_password = TextField(field_type=TextField.PASSWORD, placeholder='Password', dock=field_email.below)
    field_phone = TextField(field_type=TextField.PHONE, placeholder='Phone number', dock=field_password.below)
    field_url = TextField(field_type=TextField.URL, placeholder='URL', dock=field_phone.below)
    field_date = TextField(field_type=TextField.DATE, dock=field_url.below)
    field_time = TextField(field_type=TextField.TIME, dock=field_date.below)
    field_datetime = TextField(field_type=TextField.DATETIME, dock=field_time.below)
    field_month = TextField(field_type=TextField.MONTH, dock=field_datetime.below)
    field_week = TextField(field_type=TextField.WEEK, dock=field_month.below)
    field_color = TextField(field_type=TextField.COLOR, dock=field_week.below)

    button = Button(text='Button', dock=right_column.top_left)

    @button
    def on_click(event):
        print("Click")

run(setup)
