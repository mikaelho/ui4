import pytest
from selenium.webdriver.common.keys import Keys

from ui4 import TextField
from ui4 import View
from ui4.core import delay


def test_basics(get_app, views, driver, js_dimensions, js_style, does_not_happen, expect):
    def setup(root):
        rootlike = View(dock=root.center, width=600, height=400)

        views.textfield = TextField(placeholder='Enter text', dock=rootlike.center)

        @views.textfield
        def on_change(view):
            pass

    with get_app(setup):
        x, y, w, h = js_dimensions(views.textfield.id)
        assert pytest.approx(x + w / 2, abs=1) == 300
        assert pytest.approx(y + h / 2, abs=1) == 200

        textfield = driver.find_element_by_id(views.textfield.id)
        textfield.send_keys('ABC')

        assert does_not_happen(lambda: views.textfield.value == 'ABC', 0.1)

        textfield.send_keys(Keys.ENTER)

        assert expect(lambda: views.textfield.value == 'ABC')


def test_input_events(get_app, views, driver, expect):

    def setup(root):
        views.textfield = TextField(placeholder='Enter text', dock=root.center)
        views.textfield.counter = 0

        @views.textfield
        def on_input(view):
            views.textfield.counter += 1

    with get_app(setup):
        driver.find_element_by_id(views.textfield.id).send_keys('ABC')  # No enter needed
        assert expect(lambda: views.textfield.value == 'ABC')
        assert views.textfield.counter > 1  # Separate event for each keypress (or so)


def test_input_events_with_delay(get_app, views, driver, expect):
    def setup(root):
        views.textfield = TextField(placeholder='Enter text', dock=root.center)
        views.textfield.counter = 0

        @views.textfield
        @delay
        def on_input(view):
            view.counter += 1

    with get_app(setup):
        driver.find_element_by_id(views.textfield.id).send_keys('ABC')
        assert expect(lambda: views.textfield.value == 'ABC')
        assert views.textfield.counter == 1  # Only one event due to the delayed sending