# mimerender

mimerender is a Python module for RESTful HTTP Content Negotiation.

It acts as a decorator that wraps a HTTP request handler to select the correct render function for a given HTTP Accept header. It uses [mimeparse](http://code.google.com/p/mimeparse) to parse the accept string and select the best available representation.

Support for [webapp2](http://webapp-improved.appspot.com/) ([Google App Engine](https://developers.google.com/appengine/)), [web.py](http://webpy.org), [Flask](http://flask.pocoo.org) and [Bottle](http://bottlepy.org) is available out of the box and it's easy to add support for your favourite framework, just extend the `MimeRenderBase` class.

Build status at [Travis CI](http://travis-ci.org/): [![Build Status](https://secure.travis-ci.org/martinblech/mimerender.png)](http://travis-ci.org/martinblech/mimerender)

You can read the full documentation at [rtfd.org](http://mimerender.rtfd.org).

mimerender is released under the MIT License. A copy is included as `LICENSE`.

## Example (Flask):

```python
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
```

Then you can do:

```sh
$ curl -i -H "Accept: application/html" localhost:8080/x
$ curl -i -H "Accept: application/xml" localhost:8080/x
$ curl -i -H "Accept: application/json" localhost:8080/x
$ curl -i -H "Accept: text/plain" localhost:8080/x
```

and get results that make sense.

In the `examples` directory you will find examples for all the other supported frameworks.

## How to get it

mimerender is in [PyPI](http://pypi.python.org/pypi/mimerender), so it's as easy as doing:

```sh
$ pip install mimerender
```
