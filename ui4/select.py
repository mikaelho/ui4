from string import Template

from ui4.core import Core
from ui4.view import View


class Select(View):
    
    _template = Template(
        '<select id="$id" name="$id" class="$viewclass" '
        '$rendered_attributes $oob hx-swap="none">'
        '$options</select>'
    )

    def __init__(self, options=None, **kwargs):
        super().__init__(**kwargs)
        self.options = options or []
        
    options = Core._prop('options')
    
    def _render_options(self):
        """
        List of options
        - List of (display, value) tuples
        - List of section lists
        """

