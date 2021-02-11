from ui4.view import View


class Button(View):
    
    def _render_this(self, fixed_styles, self_styles, children_rendered):
        return (
            f'<button id="{self.id}" '
            f'style="{fixed_styles}'
            f'{self_styles}">'
            f'{children_rendered}'
            '</button>'
        )
