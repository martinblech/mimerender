"""mimerender example for Bottle. Run this server and then try:

    $ curl -H "Accept: application/html" localhost:8080/x
    $ curl -H "Accept: application/xml" localhost:8080/x
    $ curl -H "Accept: application/json" localhost:8080/x
    $ curl -H "Accept: text/plain" localhost:8080/x
"""
from bottle import Bottle, run
try:
    import simplejson as json
except ImportError:
    import json
import mimerender

mimerender = mimerender.BottleMimeRender()

render_xml = lambda message: '<message>%s</message>'%message
render_json = lambda **args: json.dumps(args)
render_html = lambda message: '<html><body>%s</body></html>'%message
render_txt = lambda message: message

app = Bottle()

@app.route('/')
@app.route('/<name>')
@mimerender(
    default = 'html',
    html = render_html,
    xml  = render_xml,
    json = render_json,
    txt  = render_txt
)
def greet(name='world'):
    return {'message': 'Hello, ' + name + '!'}

if __name__ == "__main__":
    run(app, host='localhost', port=8080)
