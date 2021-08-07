# -*- coding: utf-8 -*-
"""mimerender example for Flask. Run this server and then try:

    $ curl -iH "Accept: application/html" localhost:8080/x
    ...
    Content-Type: text/html
    ...
    <html><body>Hello, x!</body></html>

    $ curl -iH "Accept: application/xml" localhost:8080/x
    ...
    Content-Type: application/xml
    ...
    <message>Hello, x!</message>

    $ curl -iH "Accept: application/json" localhost:8080/x
    ...
    Content-Type: application/json
    ...
    {"message": "Hello, x!"}

    $ curl -iH "Accept: text/plain" localhost:8080/x
    ...
    Content-Type: text/plain
    ...
    Hello, x!

"""
import json

from flask import Flask

import mimerender

render_xml = lambda message: "<message>%s</message>" % message
render_json = lambda **args: json.dumps(args)
render_html = lambda message: "<html><body>%s</body></html>" % message
render_txt = lambda message: message

app = Flask(__name__)


@app.route("/")
@app.route("/<name>")
@mimerender.FlaskMimeRender(
    default="html", html=render_html, xml=render_xml, json=render_json, txt=render_txt
)
def greet(name="world"):
    return {"message": "Hello, " + name + "!"}


if __name__ == "__main__":
    app.run(port=8080)
