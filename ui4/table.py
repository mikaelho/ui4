from ui4.theme import TableStyle
from ui4.view import View


class Cell(View):
    _tag = 'td'
    _css_class = 'view-float'
    style = TableStyle

    def __init__(self, padding=8, **kwargs):
        super().__init__()
        self.padding = padding
        self.apply(kwargs)


class Row(View):
    _tag = 'tr'
    _css_class = 'view-float'

    def __init__(self, row_contents=None, **kwargs):
        super().__init__()
        self.apply(kwargs)
        for cell_content in row_contents:
            cell = Cell(parent=self)
            if isinstance(cell_content, View):
                cell_content.parent = cell
            else:
                cell.text = cell_content


class HeadingRow(Row):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for cell in self.children:
            cell.bold = True


class Table(View):
    _tag = 'table'
    _css_class = 'table'
    style = TableStyle

    def __init__(self, content=None, heading_row_content=None, **kwargs):
        super().__init__()
        self.heading_row_content = heading_row_content or []
        self.content = content or []
        self.apply(kwargs)

        if heading_row_content:
            HeadingRow(parent=self, row_contents=heading_row_content)

        for row_contents in content:
            Row(parent=self, row_contents=row_contents)
