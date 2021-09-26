from ui4 import Button
from ui4 import Label
from ui4 import Switch
from ui4 import serve
from ui4 import Table


class SelectButton(Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected = False

    def on_click(self, _):
        self.selected = not self.selected
        self.parent.parent.background_color = (
            self.selected and self.style.current_theme.tinted or
            self.style.current_theme.background
        )


def setup(root):
    # Baseline fitted label
    Table(
        heading_row_content=['Select', 'Text'],
        content=[
            [SelectButton(text='▶'), Label(text='One')],
            [SelectButton(text='▶'), 'Two']
        ],
        dock=root.center,
    )

    Switch(dock=root.top_center)


serve(setup)
