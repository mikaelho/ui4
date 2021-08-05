import pathlib
import shutil
from string import Template

from pytest import fixture
from selenium.webdriver import Chrome
from selenium.webdriver import DesiredCapabilities

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
def anchor_view():
    class AnchorCore(Core):
        top = Anchors._anchorprop('top')
        bottom = Anchors._anchorprop('bottom')
        left = Anchors._anchorprop('left')
        right = Anchors._anchorprop('right')
        width = Anchors._anchorprop('width')
        height = Anchors._anchorprop('height')
        center_x = Anchors._anchorprop('center_x')
        center_y = Anchors._anchorprop('center_y')
        center = Anchors._anchorprops('center_x', 'center_y')
        top_left = Anchors._anchordock('top_left')
        
    yield AnchorCore


@fixture(scope='session')
def webdriver():
    # enable browser logging
    capabilities = DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}

    with Chrome(desired_capabilities=capabilities) as driver:
        driver.set_window_size(800, 600)

        def js_value(script):
            return  driver.execute_script((f"return {script};"))
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
            contents = content_filename and (pathlib.Path(__file__).parent / 'test_data' / content_filename).read_text()
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
def get_page(webdriver, set_up_test_page):
    def get_page_by_name(content_filename=None, gap=8):
        webdriver.get(f'file://{set_up_test_page(content_filename)}')
        assert webdriver.title == 'Test page'

        log_messages = [entry for entry in webdriver.get_log('browser') if not entry['level'] == 'INFO']
        assert not log_messages, log_messages

        return webdriver

    return get_page_by_name


@fixture
def js_value(webdriver):
    def func(script):
        return webdriver.execute_script((f"return {script};"))
    return func


@fixture
def js_dimensions(webdriver):
    def func(elem_id):
        return webdriver.execute_script(f"""
            style = window.getComputedStyle(document.getElementById('{elem_id}'));
            return [
                parseInt(style.left),
                parseInt(style.top),
                parseInt(style.width),
                parseInt(style.height)
            ];
        """)
    return func