import pytest

from ui4 import Button
from ui4 import DefaultFont
from ui4 import View
from ui4.core import delay


def test_button_layout_and_styles(get_app, views, js_dimensions, js_style):
    def setup(root):
        rootlike = View(dock=root.center, width=600, height=400)

        views.button = Button(text='Button', dock=rootlike.center)

    with get_app(setup):
        # Roundabout way to check that we are centered
        x, y, w, h = js_dimensions(views.button.id)
        assert pytest.approx(x + w/2, abs=1) == 300
        assert pytest.approx(y + h/2, abs=1) == 200

        assert js_style(views.button.id, 'fontFamily').startswith(DefaultFont.font[:5])
        assert js_style(views.button.id, 'fontSize') == f'{DefaultFont.font_m}px'


def test_button_click(get_app, views, driver, expect):
    def setup(root):
        views.button = Button(text='Click me', dock=root.center)
        views.button.was_clicked = False

        @views.button
        def on_click(data):
            views.button.was_clicked = True

    with get_app(setup):
        driver.find_element_by_id(views.button.id).click()
        assert expect(lambda: views.button.was_clicked)


def test_update_on_click(get_app, views, driver, view_has_text):
    def setup(root):
        views.button = Button(text='Click me', dock=root.center, width=150)
        views.button.was_clicked = False

        @views.button
        def on_click(view):
            views.button.text = f'{view.id} was clicked'

    with get_app(setup):
        driver.find_element_by_id(views.button.id).click()
        assert view_has_text(views.button, f'{views.button.id} was clicked')
