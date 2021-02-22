import logging
import os
import threading
import time

from pathlib import Path
from string import Template

import flask
from werkzeug.serving import make_server

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


class ServerRunner:
    
    def __init__(self, protocol, host, port, quiet=False, **kwargs):
        self.protocol = protocol
        self.host = host
        self.port = port
        
        if quiet:
            import logging
            import os
            logging.getLogger('werkzeug').disabled = True
            os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        
        self.flask = flask.Flask('ui4server', static_folder=str(Path(__file__).parent / 'static'))
        
    def run_server(self):
        try:
            self.server = ServerThread(self.flask, self.host, self.port)
            self.server.start()
        except Exception as error:
            print(error)
            raise
        
    def stop_server(self):
        self.server.shutdown()
        

class PythonistaRunner(ServerRunner):
        
    def run(self):
        import wkwebview
        
        try:
            self.run_server()
            webview = wkwebview.WKWebView()
            webview.load_url(f'{self.protocol}://{self.host}:{self.port}/', no_cache=True)
            webview.present('fullscreen')
            
            webview.wait_modal()
        finally:
            self.stop_server()
            
           
class BrowserRunner(ServerRunner):
    
    def run(self):
        import webbrowser
        
        webbrowser.open(f'{self.protocol}://{self.host}:{self.port}')
           

class App(View):
    
    _css_class = 'rootApp'
    
    def __init__(
        self, 
        name="UI4 App",
        runner_class=PythonistaRunner,
        protocol="http",
        host="127.0.0.1",
        port=8080,
        **kwargs
    ):
        super().__init__(
            **kwargs)
        self.name = name
        self.runner = runner_class(protocol, host, port)
        self.flask = self.runner.flask
        
    def run(self):
        self.runner.run()
        
    def _render(self):
        if not self.children and not self.text:
            raise ValueError('app has no content')
        else:
            page_content = super()._render()
            #print(page_content)
            return page_content

app = App()


def run():
    app.run()
    

@app.flask.route('/')
def index():
    template = Template(Path('ui4/static/index_template.html').read_text())
    index_html = template.safe_substitute(
        app_name=app.name,
        content=app._render()
    )
    View._dirties = set()
    #print(index_html)
    return index_html
    
@app.flask.route('/ui4')
def send_js():
    return app.flask.send_static_file('ui4.js')
    
@app.flask.route('/event')
def handle_event():
    view_id = flask.request.args.get('id')
    view = View._views.get(view_id)
    return view and view._process_event(flask.request.args.get('event_name', 'click'))

