import json
import threading
import uuid

from pathlib import Path
from string import Template
import urllib.parse

import flask
from werkzeug.serving import make_server

from ui4.core import Identity
from ui4.view import View


class ServerThread(threading.Thread):
    
    def __init__(self, flask_app, host, port):
        threading.Thread.__init__(self)
        self.server = make_server(host, port, flask_app)
        self.context = flask_app.app_context()
        self.context.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


class FlaskRunner:
    
    def __init__(self, protocol, host, port, quiet=False, **kwargs):
        import os
        self.protocol = protocol
        self.host = host
        self.port = port
        
        if quiet:
            import logging
            logging.getLogger('werkzeug').disabled = True
            os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        
        self.flask = flask.Flask(
            'ui4server', 
            static_folder=str(Path(__file__).parent / 'static')
        )
        self.flask.secret_key = os.urandom(24)
        Identity.get_user_id = self.current_user_id
        
        self.flask.add_url_rule(
            '/',
            'index',
            self.index,
        )
        self.flask.add_url_rule(
            '/ui4',
            'send_js',
            self.send_js,
        )
        self.flask.add_url_rule(
            '/event',
            'handle_event', 
            self.handle_event, 
            methods=['GET', 'POST'],
        )
        self.flask.add_url_rule(
            '/loop',
            'event_loop',
            self.event_loop,
            methods=['GET', 'POST'],
        )
        
    def run_server(self):
        try:
            self.server = ServerThread(self.flask, self.host, self.port)
            self.server.start()
        except Exception as error:
            print(error)
            raise
        
    def stop_server(self):
        self.server.shutdown()
        
    @staticmethod
    def current_user_id():
        return flask.session['user_id']
        
    def index(self):
        user_id = flask.session.setdefault('user_id', uuid.uuid4())
        root = Root()
        self._setup_func(root)
        template = Template(Path('ui4/static/index_template.html').read_text())
        index_html = template.safe_substitute(
            app_name=self.app.name,
            gap=self.app.gap,
            content=root._render()
        )
        View._clear_dirties()
        print(index_html)
        return index_html
    
    def send_js(self):
        return self.flask.send_static_file('ui4.js')
    
    def handle_event(self):
        view_id = flask.request.headers.get('Hx-Trigger')
        event_header = urllib.parse.unquote(flask.request.headers.get('Triggering-Event'))
        event_name = json.loads(event_header)['type']
        view = View.get_view(view_id)
        value = flask.request.values.get(view_id, view)
        update_html = view._process_event(event_name, value)
        print(update_html)
        return update_html
        
    def event_loop(self):
        view_id = flask.request.headers.get('Hx-Trigger')
        event_header = json.loads(urllib.parse.unquote(
            flask.request.headers.get('Triggering-Event')
        ))
        animation_id = event_header['detail']['animationID']
        update_html = View._process_event_loop(animation_id)
        # print(update_html)
        return update_html
        

class PythonistaRunner(FlaskRunner):

    def __init__(self, protocol, host, port, quiet=False, **kwargs):
        import wkwebview
        super().__init__(protocol, host, port, quiet, **kwargs)

    def run(self, cache=False):
        import wkwebview

        try:
            self.run_server()
            webview = wkwebview.WKWebView()
            webview.load_url(
                f'{self.protocol}://{self.host}:{self.port}/', 
                no_cache=not cache)
            webview.present('fullscreen')
            
            webview.wait_modal()
        finally:
            self.stop_server()
            
           
class BrowserRunner(FlaskRunner):
    
    def run(self):
        import webbrowser

        self.run_server()

        webbrowser.open(f'{self.protocol}://{self.host}:{self.port}')
           
           
class Root(View):
    
    _css_class = 'rootApp'
    
    def _render(self, oob=''):
        if not self.children and not self.text:
            raise ValueError('app has no content')
        else:
            page_content = super()._render(oob)
            #print(page_content)
            return page_content


class App:
    
    def __init__(
        self, 
        name="UI4 App",
        gap=None,
        runner_class=None,
        protocol="http",
        host="127.0.0.1",
        port=8080,
        **kwargs
    ):
        super().__init__(
            **kwargs)
        self.name = name
        self.gap = gap is None and 8 or gap
        self.runner = (
            runner_class and runner_class(protocol, host, port) or 
            self._detect_runner(protocol, host, port)
        )
        self.runner.app = self
        #self.flask = self.runner.flask

    def _detect_runner(self, protocol, host, port):
        try:
            return PythonistaRunner(protocol, host, port)
        except ImportError:
            pass

        return BrowserRunner(protocol, host, port)


    def run(self, setup_func):
        self.runner._setup_func = setup_func
        self.runner.run()


def run(setup_func, gap=None, **kwargs):
    app = App(gap=gap, **kwargs)
    app.run(setup_func)

