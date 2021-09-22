from string import Template

from ui4 import TableStyle
from ui4 import View


class Cell(View):
    _css_class = 'view-float'
    _template = Template(
        '<td id="$id" class="$viewclass" '
        '$rendered_attributes $oob hx-swap="none">$content</td>'
    )
    style = TableStyle

    def __init__(self, padding=8, **kwargs):
        super().__init__(self)
        self.padding = padding
        self.apply(kwargs)


class Row(View):
    _css_class = 'view-float'
    _template = Template(
        '<tr id="$id" class="$viewclass" '
        '$rendered_attributes $oob hx-swap="none">$content</tr>'
    )

    def __init__(self, row_contents=None, **kwargs):
        super().__init__(self)
        self.apply(kwargs)
        for cell_content in row_contents:
            cell = Cell(parent=self)
            if isinstance(cell_content, View):
                cell_content.parent = cell
                cell_content._css_class = 'view-float'
            else:
                cell.text = cell_content


class HeadingRow(Row):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for cell in self.children:
            cell.bold = True


class Table(View):
    _template = Template(
        '<table id="$id" class="$viewclass" '
        '$rendered_attributes $oob hx-swap="none">$content</table>'
    )
    _css_class = 'table'
    style = TableStyle

    def __init__(self, content=None, heading_row_content=None, **kwargs):
        super().__init__(self)
        self.heading_row_content = heading_row_content or []
        self.content = content or []
        self.apply(kwargs)

        if heading_row_content:
            HeadingRow(parent=self, row_contents=heading_row_content)

        for row_contents in content:
            Row(parent=self, row_contents=row_contents)

    # def _render_result(self, rendered_attributes, htmx_oob, rendered_children):
    #     rendered_table_content = ''.join(self._render_row(row_content) for row_content in self.content)
    #     return super()._render_result(rendered_attributes, htmx_oob, rendered_table_content)
    #
    # def _render_row(self, row_content) -> str:
    #     row_template = Template('<tr>$row_content</tr>')
    #     row_result = ''.join(self._render_cell(cell_content) for cell_content in row_content)
    #     return row_template.safe_substitute(row_content=row_result)
    #
    # def _render_cell(self, cell_content) -> str:
    #     cell = Cell(parent=self, text=cell_content)
    #     return cell._render()
