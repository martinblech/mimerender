"""mimerender exception mapping example for webapp2. Run this server and
then try:

    $ curl -H "Accept: application/xml" localhost:8080/1
    $ curl -H "Accept: application/xml" localhost:8080/2
    $ curl -H "Accept: application/xml" localhost:8080/abc
    $ curl -H "Accept: application/json" localhost:8080/1
    $ curl -H "Accept: application/json" localhost:8080/2
    $ curl -H "Accept: application/json" localhost:8080/abc
"""
import webapp2
try:
    import simplejson as json
except ImportError:
    import json
import mimerender

mimerender = mimerender.Webapp2MimeRender()

render_xml = lambda message: '<message>%s</message>'%message
render_json = lambda **kwargs: json.dumps(kwargs)

render_xml_exception = lambda exception: '<exception>%s</exception>'%exception
render_json_exception = lambda exception: json.dumps(exception.args)

class NotFound(Exception): pass

class Greet(webapp2.RequestHandler):
    @mimerender.map_exceptions(
        mapping=(
            (ValueError, '500 Internal Server Error'),
            (NotFound, '404 Not Found')
        ),
        xml  = render_xml_exception,
        json = render_json_exception,
    )
    @mimerender(
        xml  = render_xml,
        json = render_json,
    )
    def get(self, id_):
        int_id = int(id_)
        if int_id != 1:
            raise NotFound('could not find item with id = %d' % int_id)
        return dict(message='found it!')

app = webapp2.WSGIApplication([
    ('/(.*)', Greet),
], debug=True)

def main():
    from paste import httpserver
    httpserver.serve(app, host='127.0.0.1', port='8080')

if __name__ == '__main__':
    main()
