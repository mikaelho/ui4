
import pytest

from ui4 import Label
from ui4 import View
from ui4 import at_most


def test_view_basics(get_app, views, js_dimensions, js_style, js_with_stack):
    def setup(root):
        rootlike = View(dock=root.center, width=600, height=400)

        # Baseline fitted label
        views.basic = Label(text='Label with text', dock=rootlike.center, background_color='darkseagreen')

        # Docking
        views.docked = Label(text='Label with text', dock=rootlike.top, background_color='darkseagreen')

        # Fixing width flexes height
        views.fixed_width = Label(
            text='A little more text to make things interesting',
            background_color='darkseagreen',
            dock=rootlike.bottom_center,
            width=150,
        )

        # Limiting (capping) works as well
        views.limited = Label(text='Label with text', dock=rootlike.right_center, background_color='darkseagreen')
        views.limited.width = at_most(80)

        # For height, it essentially just fixes the height
        views.fixed_height = Label(
            text='A little more text to fit',
            background_color='darkseagreen',
            dock=rootlike.left_center,
            height=50,
        )

        # Fixing both dimensions truncates the text if needed, but no ellipsis :-(
        views.truncated_text = Label(
            text='Just too much text that gets neatly cut at the end',
            background_color='darkseagreen',
            dock=rootlike.bottom_right,
            width=150,
            height=50,
        )

        # Different text alignment
        views.aligned_top_right = Label(
            text='Top right corner',
            alignment=('top', 'right'),
            background_color='darkseagreen',
            dock=rootlike.bottom_left,
            width=150,
            height=150,
        )

    with get_app(setup):

        # BASIC

        # Roundabout way to check that we are centered
        x, y, w, h = js_dimensions(views.basic.id)
        assert pytest.approx(x + w/2, abs=1) == 300
        assert pytest.approx(y + h/2, abs=1) == 200
        # Label text views are relative and managed by flex, so have no left or top set
        text_dimensions = js_dimensions(views.basic._text_view.id)
        assert text_dimensions.width == w-16
        assert text_dimensions.height == h-16
        # Style is picked up
        assert js_style(views.basic._text_view.id, 'fontFamily').startswith('-apple')

        # DOCKED
        assert js_dimensions(views.docked.id) == (8, 8, 584, 33)

        # FIXED WIDTH
        x, y, w, h = js_dimensions(views.fixed_width.id)
        assert x == 225
        assert y == 400 - h - 8
        assert w == 150
        assert h > 33

        # CAPPED WITH
        x, y, w, h = js_dimensions(views.limited.id)
        assert x >= 600 - 80 - 8
        assert x + w == 600 - 8
        assert h > 33

        # FIXED HEIGHT
        assert js_dimensions(views.fixed_height.id).width > 50

        # TRUNCATED TEXT
        text_content_id = views.truncated_text._text_view.id
        visible_height, full_height = js_with_stack(
            f'el = document.getElementById("{text_content_id}"); return [el.clientHeight, el.scrollHeight];'
        )
        assert visible_height < full_height
        assert visible_height == 34

        # ALIGNED TOP RIGHT
        # Check correct flex alignment
        assert js_style(views.aligned_top_right.id, 'alignItems') == 'flex-end'
        assert js_style(views.aligned_top_right.id, 'justifyContent') == 'flex-start'
