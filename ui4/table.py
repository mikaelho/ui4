from string import Template

from ui4 import Label
from ui4 import TableStyle
from ui4 import View


class TableCell(View):
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


class Table(View):
    _template = Template(
        '<table id="$id" class="$viewclass" '
        '$rendered_attributes $oob hx-swap="none">$content</table>'
    )
    _css_class = 'table'
    style = TableStyle

    def __init__(self, content=None, **kwargs):
        super().__init__(self)
        self.content = content or []
        self.apply(kwargs)

    def _render_result(self, rendered_attributes, htmx_oob, rendered_children):
        rendered_table_content = ''.join(self._render_row(row_content) for row_content in self.content)
        return super()._render_result(rendered_attributes, htmx_oob, rendered_table_content)

    def _render_row(self, row_content) -> str:
        row_template = Template('<tr>$row_content</tr>')
        row_result = ''.join(self._render_cell(cell_content) for cell_content in row_content)
        return row_template.safe_substitute(row_content=row_result)

    def _render_cell(self, cell_content) -> str:
        cell = TableCell(parent=self, text=cell_content)
        return cell._render()
        # cell_template = Template('<td>$cell_content</td>')
        #return cell_template.safe_substitute(cell_content=cell_content)
