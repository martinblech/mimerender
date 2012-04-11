# mimerender: Python module for RESTful resource variant selection using the HTTP Accept header

This module provides a decorator that wraps a HTTP request handler to select the correct render function for a given HTTP Accept header. It uses [mimeparse](code.google.com/p/mimeparse) to parse the accept string and select the best available representation.

It supports [web.py](webpy.org), [Flask](flask.pocoo.org) and [Bottle](bottlepy.org) out of the box and it's easy to add support for your favourite framework, just extend the `MimeRenderBase` class.

## Example (Flask):

    from flask import Flask
    import json
    import mimerender

    mimerender = mimerender.FlaskMimeRender()

    render_xml = lambda message: '<message>%s</message>'%message
    render_json = lambda **args: json.dumps(args)
    render_html = lambda message: '<html><body>%s</body></html>'%message
    render_txt = lambda message: message

    app = Flask(__name__)

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
        app.run(port=8080)

Then you can do:

    $ curl -i -H "Accept: application/html" localhost:8080/x
    $ curl -i -H "Accept: application/xml" localhost:8080/x
    $ curl -i -H "Accept: application/json" localhost:8080/x
    $ curl -i -H "Accept: text/plain" localhost:8080/x

and get results that make sense.

In the `examples` directory you will find examples for `web.py` and `Bottle` as well)

## How to get it

mimerender is in [PyPI](pypi.python.org/pypi/mimerender), so it's as easy as doing:

    $ pip install mimerender
