import pathlib
import shutil
from collections import namedtuple
from contextlib import contextmanager
from string import Template

from pytest import fixture
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import text_to_be_present_in_element
from selenium.webdriver.support.wait import WebDriverWait

from ui4.app import serve
from ui4.core import Anchors
from ui4.core import Core


@fixture
def test_data_dir():
    return str(pathlib.Path(__file__).parent / 'test_data')


@fixture(autouse=True)
def clean_state():
    Core._clean_state()


@fixture
def is_view_id():
    class IsViewID:
        """
        Utility class for checking that a value is a valid view ID.
        """
        def __eq__(self, other):
            if other.startswith('id'):
                try:
                    int(other[len('id'):])
                    return True
                except:
                    return False
            return False
    yield IsViewID()


@fixture
def constraints():
    return lambda view: view._render_anchors()['ui4']


@fixture(scope='class')
def constraints_class(request):
    request.cls.constraints = lambda cls, view: view._render_anchors()['ui4']

    
@fixture
def anchor_view():
    class AnchorCore(Core):
        top = Anchors._anchorprop('top')
        bottom = Anchors._anchorprop('bottom')
        left = Anchors._anchorprop('left')
        right = Anchors._anchorprop('right')
        width = Anchors._anchorprop('width')
        height = Anchors._anchorprop('height')
        center_x = Anchors._anchorprop('centerX')
        center_y = Anchors._anchorprop('centerY')
        center = Anchors._anchorprops('center_x', 'center_y')
        top_left = Anchors._anchordock('top_left')

    yield AnchorCore


# BROWSER AUTOMATION

def chrome_setup():
    # enable browser logging
    capabilities = webdriver.DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}

    driver = webdriver.Chrome(desired_capabilities=capabilities)
    driver.logs = lambda: [entry for entry in driver.get_log('browser') if entry['level'] != 'INFO']

    return driver


def safari_setup():
    driver = webdriver.Safari()
    driver.logs = lambda: []

    return driver


# @fixture(scope='session', params=[chrome_setup, safari_setup])
@fixture(scope='session', params=[safari_setup])
def driver(request):

    with request.param() as driver:
        driver.set_window_size(800, 600)

        def js_value(script):
            return driver.execute_script(f"return {script};")
        driver.js_value = js_value

        yield driver


@fixture
def set_up_test_page(tmp_path):
    def set_up(content_filename=None, gap=8):
        statics = pathlib.Path(__file__).parent.parent / 'ui4' / 'static'
        shutil.copy(statics / 'ui4parser.js', tmp_path)
        shutil.copy(statics / 'ui4.js', tmp_path)
        template = Template((statics / 'index_template.html').read_text())

        if content_filename:
            contents = content_filename and (
                    pathlib.Path(__file__).parent / 'test_browser' / 'test_data' / content_filename
            ).read_text()
        else:
            contents = ''

        index_html = template.safe_substitute(
            app_name='Test page',
            gap=gap,
            content=contents,
        )
        index_file = tmp_path / 'index.html'
        index_file.write_text(index_html)
        return str(index_file)

    return set_up


@fixture
def get_page(driver, set_up_test_page):
    def get_page_by_name(content_filename=None, gap=8):
        driver.get(f'file://{set_up_test_page(content_filename)}')
        assert driver.title == 'Test page'

        log_messages = driver.logs()
        assert not log_messages, log_messages

        return driver

    return get_page_by_name


@fixture
def get_app(driver):
    @contextmanager
    def start_server_and_open_index_page(func, gap=None):
        app = None
        try:
            app = serve(func, gap)
            driver.get('http://127.0.0.1:8080/')

            if app.runner.server.exception:
                raise app.runner.server.exception

            log_messages = driver.logs()
            assert not log_messages, log_messages

            yield driver

        finally:
            if app:
                app.stop()

    return start_server_and_open_index_page


@fixture
def views():
    class Views:
        def _apply(self, **kwargs):
            for attribute in dir(self):
                if not attribute.startswith('_'):
                    view = getattr(self, attribute)
                    for key, value in kwargs.items():
                        if key == 'text':
                            value = attribute
                        setattr(view, key, value)

    return Views()


@fixture
def js_with_stack(driver):
    def func(script):
        return driver.execute_script(f"""
            try {{
                {script}
            }} catch (err) {{
                return err.stack;
            }}
        """)

    return func


@fixture
def js_value(js_with_stack):
    def func(script):
        return js_with_stack(f"return {script};")
    return func


@fixture
def js_style(js_value):
    def func(elem_id, style_name):
        return js_value(f'window.getComputedStyle(document.getElementById("{elem_id}")).{style_name}')
    return func


@fixture
def js_text(js_value):
    def func(elem_id):
        return js_value(f'document.getElementById("{elem_id}").innerText')
    return func


@fixture
def js_dimensions(js_with_stack):
    Dimensions = namedtuple('Dimensions', 'left top width height')

    def func(elem_id: str) -> tuple:
        return Dimensions(*js_with_stack(f"""
            style = window.getComputedStyle(document.getElementById('{elem_id}'));
            return [
                parseInt(style.left),
                parseInt(style.top),
                parseInt(style.width),
                parseInt(style.height)
            ];
        """))

    return func


@fixture
def view_has_text(driver):
    def func(view, text):
        try:
            element = WebDriverWait(driver, 1, 0.1).until(
                text_to_be_present_in_element((By.ID, view.id), text)
            )
            return element
        except TimeoutException:
            return False
    return func


@fixture
def expect(driver):
    class func_to_be_true:
        """ A Selenium expectation that the function will return a True value. """

        def __init__(self, func):
            self.func = func

        def __call__(self, driver):
            return self.func()

    def func(expect_func, how_long_to_try=1, time_between_attempts=0.1):
        try:
            element = WebDriverWait(driver, 1, 0.1).until(
                func_to_be_true(expect_func)
            )
            return element
        except TimeoutException:
            return False
    return func


@fixture
def does_not_happen(expect):
    def func(expect_func, how_long_to_try=1, time_between_attempts=0.1):
        return expect(expect_func, how_long_to_try, time_between_attempts) == False
    return func