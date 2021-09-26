import time

from ui4 import View
from ui4.table import Table


def test_table_layout(get_app, views, js_dimensions, js_style, js_with_stack):
    def setup(root):
        rootlike = View(dock=root.center, width=600, height=400)

        # Baseline fitted label
        views.basic = Table(content=[['One', 'Two'], ['Three', 'Four']], dock=rootlike.center)

    with get_app(setup):
        pass
        #time.sleep(5)
        # ...

