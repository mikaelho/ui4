from ui4.theme import CardStyle
from ui4.view import View


class Card(View):
    
    style = CardStyle
    
    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)
        self.title_view = View(
            chrome=True,
            text=title,
            gap=0,
        )
        self.title_view.dock = self.top
        self.container = View(gap=0)
        self.container.dock = self.bottom
        self.container.top = self.title_view.bottom

