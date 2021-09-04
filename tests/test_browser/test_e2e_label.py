import time

import pytest

from ui4 import BaseStyle
from ui4 import Label
from ui4 import View
from ui4 import at_most


def test_view_basics(get_app, views, js_dimensions, js_style):
    def setup(root):
        rootlike = View(dock=root.center, width=600, height=400)

        # Baseline fitted label
        views.label1 = Label(text='Label with text', dock=rootlike.center, background_color='darkseagreen')

        # Limiting one dimension flexes the other if needed
        views.label1b = Label(text='Label with text', dock=rootlike.right_center, background_color='darkseagreen')
        views.label1b.width = at_most(80)

        # Docking requires releasing the fit
        views.label2 = Label(text='Label with text', background_color='darkseagreen')
        views.label2.width = None
        views.label2.dock = rootlike.top

        # Fixing one dimension flexes the other - width locked
        views.label3 = Label(
            text='A little more text to make things interesting',
            background_color='darkseagreen',
            dock=rootlike.bottom_center,
            width=150,
        )

        # Fixing one dimension flexes the other - height locked
        views.label4 = Label(
            text='A little more text to fit',
            background_color='darkseagreen',
            dock=rootlike.left_center,
            height=50,
        )
        views.label4._text_view.background_color = 'white'

        # Fixing both dimensions truncates the text if needed
        views.label_not_numbered__how_to_test_questionmark = Label(
            text='Just too much text that gets neatly cut at the end',
            background_color='darkseagreen',
            dock=rootlike.bottom_right,
            width=150,
            height=50,
        )

        # Different text alignment
        views.label5 = Label(
            text='Top right corner',
            alignment=('top', 'right'),
            background_color='darkseagreen',
            dock=rootlike.bottom_left,
            width=150,
            height=150,
        )

    with get_app(setup):
        time.sleep(10)

        x, y, w, h = js_dimensions(views.label1.id)

        # Roundabout way to check that we are centered
        assert pytest.approx(x + w/2, 1) == 300
        assert pytest.approx(y + h/2, 1) == 200

        assert js_dimensions(views.label1._text_view.id) == pytest.approx((8, 8, w-16, h-16), 1)
        assert js_style(views.label1._text_view.id, 'fontFamily').startswith('-apple')

        assert js_dimensions(views.label2.id) == (8, 8, 584, 33)

        x, y, w, h = js_dimensions(views.label3.id)
        assert x == 225
        assert w == 150
        assert h > 50
        assert y == 400 - h - 8

        x, y, w, h = js_dimensions(views.label5.id)
        xt, yt, wt, ht = js_dimensions(views.label5._text_view.id)
        assert xt == pytest.approx(w - wt - 8, 1)
        assert yt == 8


def test_padding_alternative(get_app, views, js_dimensions, js_style):
    def setup(root):
        rootlike = View(dock=root.center, width=600, height=400)

        basic_parameters = {
            'style': BaseStyle,
            'padding': 8,
            'background_color': 'darkseagreen',
        }

        basic_without_padding = basic_parameters.copy()
        basic_without_padding.pop('padding')

        # Baseline fitted label
        views.label1 = View(
            text='Label with text',
            _css_class='label',
            dock=rootlike.center,
            align='center',
            **basic_parameters,
        )

        # Limiting one dimension flexes the other if needed
        views.label1b = View(
            text='Label with text',
            _css_class='label',
            width=at_most(80),
            align='center',
            dock=rootlike.right_center,
            **basic_parameters,
        )

        views.label2 = View(
            text='Label with text',
            _css_class='label',
            align='center',
            dock=rootlike.top,
            **basic_parameters,
        )

        # Fixing one dimension flexes the other - width locked
        views.label3 = View(
            text='A little more text to make things interesting',
            _css_class='label',
            dock=rootlike.bottom_center,
            align='center',
            width=150,
            **basic_parameters,
        )

        # Fixing one dimension flexes the other - height locked
        views.label4 = View(
            text='A little more text to fit here',
            _css_class='label',
            dock=rootlike.left_center,
            height=50,
            padding=8,
            align='right',
            **basic_without_padding,
        )

        # Fixing both dimensions truncates the text if needed
        views.label_not_numbered__how_to_test_questionmark = View(
            text='Just too much text that gets neatly cut at the end',
            _css_class='label',
            dock=rootlike.bottom_right,
            width=150,
            height=50,
            **basic_parameters,
        )

        # Different text alignment
        views.label5 = View(
            text='Top bottom corner',
            _css_class='label',
            dock=rootlike.bottom_left,
            width=150,
            height=150,
            padding=8,
            align='right',
            **basic_without_padding
        )

    with get_app(setup):
        time.sleep(10)

        x, y, w, h = js_dimensions(views.label1.id)

        # Roundabout way to check that we are centered
        assert pytest.approx(x + w/2, 1) == 300
        assert pytest.approx(y + h/2, 1) == 200

        assert js_dimensions(views.label1._text_view.id) == pytest.approx((8, 8, w-16, h-16), 1)
        assert js_style(views.label1._text_view.id, 'fontFamily').startswith('-apple')

        assert js_dimensions(views.label2.id) == (8, 8, 584, 33)

        x, y, w, h = js_dimensions(views.label3.id)
        assert x == 225
        assert w == 150
        assert h > 50
        assert y == 400 - h - 8

        x, y, w, h = js_dimensions(views.label5.id)
        xt, yt, wt, ht = js_dimensions(views.label5._text_view.id)
        assert xt == pytest.approx(w - wt - 8, 1)
        assert yt == 8
