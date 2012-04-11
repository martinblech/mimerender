"""
RESTful resource variant selection using the HTTP Accept header.
"""

__version__   = '0.3'
__author__    = 'Martin Blech <martinblech@gmail.com>'
__license__   = 'MIT'

import mimeparse

# ctx = web.threadeddict()

class MimeRenderException(Exception): pass

XML   = 'xml'
JSON  = 'json'
YAML  = 'yaml'
XHTML = 'xhtml'
HTML  = 'html'
TXT   = 'txt'
CSV   = 'csv'
TSV   = 'tsv'
RSS   = 'rss'
RDF   = 'rdf'
ATOM  = 'atom'
M3U   = 'm3u'
PLS   = 'pls'
XSPF  = 'xspf'
ICAL  = 'ical'
KML   = 'kml'
KMZ   = 'kmz'

_MIME_TYPES = {
    XML:   ('application/xml', 'text/xml', 'application/x-xml',),
    JSON:  ('application/json',),
    YAML:  ('application/x-yaml', 'text/yaml',),
    XHTML: ('application/xhtml+xml',),
    HTML:  ('text/html',),
    TXT:   ('text/plain',),
    CSV:   ('text/csv',),
    TSV:   ('text/tab-separated-values',),
    RSS:   ('application/rss+xml',),
    RDF:   ('application/rdf+xml',),
    ATOM:  ('application/atom+xml',),
    M3U:   ('audio/x-mpegurl', 'application/x-winamp-playlist', 'audio/mpeg-url', 'audio/mpegurl',),
    PLS:   ('audio/x-scpls',),
    XSPF:  ('application/xspf+xml',),
    ICAL:  ('text/calendar',),
    KML:   ('application/vnd.google-earth.kml+xml',),
    KMZ:   ('application/vnd.google-earth.kmz',),
}

def register_mime(shortname, mime_types):
    """
    Register a new mime type.
    Usage example:
        mimerender.register_mime('svg', ('application/x-svg', 'application/svg+xml',))
    After this you can do:
        @mimerender.mimerender(svg=render_svg)
        def GET(...
            ...
    """
    if shortname in _MIME_TYPES:
        raise MimeRenderException('"%s" has already been registered'%shortname)
    _MIME_TYPES[shortname] = mime_types

def _get_mime_types(shortname):
    try:
        return _MIME_TYPES[shortname]
    except KeyError:
        raise MimeRenderException('No known mime types for "%s"'%shortname)

def _get_short_mime(mime):
    for shortmime, mimes in _MIME_TYPES.items():
        if mime in mimes:
            return shortmime
    raise MimeRenderException('No short mime for type "%s"' % mime)

def _best_mime(supported, accept_string=None):
    if accept_string is None:
        return None
    return mimeparse.best_match(supported, accept_string)

class MimeRenderBase(object):

    def __init__(self, global_default=None, global_override_arg_idx=None,
            global_override_input_key=None, global_charset=None):
        self.global_default = global_default
        self.global_override_arg_idx = global_override_arg_idx
        self.global_override_input_key = global_override_input_key
        self.global_charset = global_charset

    def __call__(self, default=None, override_arg_idx=None,
            override_input_key=None, charset=None, **renderers):
        """
        Usage:
            @mimerender(default='xml', override_arg_idx=-1, override_input_key='format', , <renderers>)
            GET(self, ...) (or POST, etc.)
            
        The decorated function must return a dict with the objects necessary to
        render the final result to the user. The selected renderer will be 
        called with the map contents as keyword arguments.
        If override_arg_idx isn't None, the wrapped function's positional
        argument at that index will be used instead of the Accept header.
        override_input_key works the same way, but with web.input().
        
        Example:

            @mimerender(
                default = 'xml',
                override_arg_idx = -1,
                override_input_key = 'format',
                xhtml   = xhtml_templates.greet,
                html    = xhtml_templates.greet,
                xml     = xml_templates.greet,
                json    = json_render,
                yaml    = json_render,
                txt     = json_render,
            )
            def greet(self, param):
                message = 'Hello, %s!'%param
                return {'message':message}
        """
        if not renderers:
            raise ValueError('need at least one renderer')

        def get_renderer(mime):
            try:
                return renderer_dict[mime]
            except KeyError:
                raise MimeRenderException('No renderer for mime "%s"'%mime)
        
        if not default: default = self.global_default
        if not override_arg_idx: override_arg_idx = self.global_override_arg_idx
        if not override_input_key: override_input_key = self.global_override_input_key
        if not charset: charset = self.global_charset
        
        supported = list()
        renderer_dict = dict()
        for shortname, renderer in renderers.items():
            for mime in _get_mime_types(shortname):
                supported.append(mime)
                renderer_dict[mime] = renderer
        if default:
            default_mime = _get_mime_types(default)[0]
            default_renderer = get_renderer(default_mime)
        else:
            default_mime, default_renderer = renderer_dict.items()[0]
        
        def wrap(target):
            def wrapper(*args, **kwargs):
                mime = None
                shortmime = None
                if override_arg_idx != None:
                    shortmime = args[override_arg_idx]
                if not shortmime and override_input_key:
                    shortmime = self.get_request_parameter(override_input_key)
                if shortmime: mime = _get_mime_types(shortmime)[0]
                if not mime:
                    mime = _best_mime(supported, self.get_accept_header())
                if mime:
                    renderer = get_renderer(mime)
                else:
                    mime, renderer = default_mime, default_renderer
                if not shortmime: shortmime = _get_short_mime(mime)
                context_vars = dict(
                        mimerender_shortmime=shortmime,
                        mimerender_mime=mime,
                        mimerender_renderer=renderer)
                for key, value in context_vars.items():
                    self.set_context_var(key, value)
                try:
                    result = target(*args, **kwargs)
                finally:
                    for key in context_vars.keys():
                        self.clear_context_var(key)
                content_type = mime
                if charset: content_type += '; charset=%s' % charset
                content = renderer(**result)
                return self.make_response(content, content_type)
            return wrapper
        
        return wrap

    def get_request_parameter(self, key, default=None):
        return default

    def get_accept_header(self, default=None):
        return default

    def set_context_var(self, key, value):
        pass

    def clear_context_var(self, key):
        pass

    def make_response(self, content, content_type):
        return content

# web.py implementation
try:
    import web
    class WebPyMimeRender(MimeRenderBase):
        def get_request_parameter(self, key, default=None):
            return web.input().get(key, default)

        def get_accept_header(self, default=None):
            return web.ctx.env.get('HTTP_ACCEPT', default)

        def set_context_var(self, key, value):
            web.ctx[key] = value

        def clear_context_var(self, key):
            del web.ctx[key]

        def make_response(self, content, content_type):
            web.header('Content-Type', content_type)
            return content

except ImportError:
    pass

# Flask implementation
try:
    import flask
    class FlaskMimeRender(MimeRenderBase):
        def get_request_parameter(self, key, default=None):
            return flask.request.values.get(key, default)

        def get_accept_header(self, default=None):
            return flask.request.headers.get('Accept', default)

        def set_context_var(self, key, value):
            flask.request.environ[key] = value

        def clear_context_var(self, key):
            del flask.request.environ[key]

        def make_response(self, content, content_type):
            response = flask.make_response(content)
            response.headers['Content-Type'] = content_type
            return response

except ImportError:
    pass

# Bottle implementation
try:
    import bottle
    class BottleMimeRender(MimeRenderBase):
        def get_request_parameter(self, key, default=None):
            return bottle.request.params.get(key, default)

        def get_accept_header(self, default=None):
            return bottle.request.headers.get('Accept', default)

        def set_context_var(self, key, value):
            bottle.request.environ[key] = value

        def clear_context_var(self, key):
            del bottle.request.environ[key]

        def make_response(self, content, content_type):
            bottle.response.content_type = content_type
            return content

except ImportError:
    pass

# unit tests
if __name__ == "__main__":
    try:
        import unittest2 as unittest
    except ImportError:
        import unittest

    class TestMimeRender(MimeRenderBase):
        def __init__(self, request_parameters=None, accept_header=None,
                *args, **kwargs):
            super(TestMimeRender, self).__init__(*args, **kwargs)
            self.request_parameters = request_parameters or {}
            self.accept_header = accept_header
            self.ctx = {}

        def get_request_parameter(self, key, default=None):
            return self.request_parameters.get(key, default)

        def get_accept_header(self, default=None):
            return self.accept_header

        def set_context_var(self, key, value):
            self.ctx[key] = value

        def clear_context_var(self, key):
            del self.ctx[key]

        def make_response(self, content, content_type):
            self.content_type = content_type
            return content

    class MimeRenderTests(unittest.TestCase):
        def test_single_variant(self):
            mimerender = TestMimeRender()
            result = mimerender(
                    xml=lambda x: '<xml>%s</xml>' % x
                    )(lambda: dict(x='test'))()
            self.assertEquals(mimerender.content_type, 'text/xml')
            self.assertEquals(result, '<xml>test</xml>')

        def test_norenderers(self):
            try:
                TestMimeRender()()
                self.fail('should fail with ValueError')
            except ValueError:
                pass

        def test_select_variant(self):
            mimerender = TestMimeRender()
            handler = mimerender(
                    default='txt',
                    override_input_key='mime',
                    txt=lambda x: 'txt:%s' %x,
                    xml=lambda x: 'xml:%s' % x,
                    json=lambda x: 'json:%s' % x,
                    html=lambda x: 'html:%s' % x,
                    )(lambda x: dict(x=x))

            result = handler('default')
            self.assertEquals(mimerender.content_type, 'text/plain')
            self.assertEquals(result, 'txt:default')

            mimerender.accept_header = 'application/xml'
            result = handler('a')
            self.assertEquals(mimerender.content_type, 'application/xml')
            self.assertEquals(result, 'xml:a')

            mimerender.accept_header = 'application/json'
            result = handler('b')
            self.assertEquals(mimerender.content_type, 'application/json')
            self.assertEquals(result, 'json:b')

            mimerender.request_parameters['mime'] = 'html'
            result = handler('c')
            self.assertEquals(mimerender.content_type, 'text/html')
            self.assertEquals(result, 'html:c')
    
    unittest.main()
