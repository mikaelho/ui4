import logging
import os
import threading
import time

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
    
    def __init__(self, host, port, quiet=False, **kwargs):
        self.host = host
        self.port = port
        
        if quiet:
            import logging
            import os
            logging.getLogger('werkzeug').disabled = True
            os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        
        self.flask = flask.Flask('ui4server')
        self.server = ServerThread(self.flask, host, port)
        self.server.start()
        
    def stop_server(self):
        self.server.shutdown()
        

class PythonistaRunner(ServerRunner):
        
    def run(self):
        import ui
        
        webview = ui.WebView()
        webview.load_html('Loading...')
        webview.load_url(f'http://127.0.0.1:{self.port}')
        webview.present('fullscreen')
        try:
            webview.wait_modal()
        finally:
            self.stop_server()
           

class App(View):
    
    _fixed_styles = 'position: absolute; width: 100%; height: 100%; background-color: palegreen;'
    
    def __init__(
        self, 
        runner_class=PythonistaRunner, 
        host="127.0.0.1",
        port=8080,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.runner = runner_class(host, port)
        self.flask = self.runner.flask
        
    def run(self):
        self.runner.run()
        
    def _render_this(self, fixed_styles, self_styles, children_rendered):
        return (
            f'<div id="{self.id}" '
            f'style="{fixed_styles}">'
            f'{children_rendered}'
            '</div>'
        )


app = App()


def run():
    app.run()
    

@app.flask.route('/')
def index():
    index_html = f"""
    <html>
        <head>
             <script src="https://unpkg.com/htmx.org@1.1.0" integrity="sha384-JVb/MVb+DiMDoxpTmoXWmMYSpQD2Z/1yiruL8+vC6Ri9lk6ORGiQqKSqfmCBbpbX" crossorigin="anonymous"></script>
             <script>
             document.body.addEventListener('htmx:configRequest', function(evt) {{
                 alert('Hou');
                    evt.detail.parameters['width'] = 'foobar'; // evt.detail.elt.width;
                }});
             alert('hougougou');
             </script>
        </head>
        <body hx-trigger="load" hx-post="/ready" hx-target="#targetdiv">
        {app._render()}
        <div id="targetdiv"></div>
        </body>
    </html>
    """
    # print(index_html)
    return index_html
    
    
@app.flask.route('/ready', methods=['POST'])
def ready():
    print(flask.request.form)
    return "This one is now loaded"

