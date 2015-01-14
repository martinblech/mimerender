"""
RESTful resource variant selection using the HTTP Accept header.
"""

__version__   = '0.5.5'
__author__    = 'Martin Blech <martinblech@gmail.com>'
__license__   = 'MIT'

import mimeparse
from functools import wraps
import re

class MimeRenderException(Exception): pass

XML   = 'xml'
JSON  = 'json'
JSONLD = 'jsonld'
JSONP = 'jsonp'
BSON  = 'bson'
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
    JSONLD: ('application/ld+json',),
    JSONP: ('application/javascript',),
    BSON:  ('application/bson',),
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

VARY_SEPARATOR = re.compile(r',\s*')
def _fix_headers(headers, content_type):
    fixed_headers = []
    found_vary = False
    found_content_type = False
    for k, v in headers:
        if k.lower() == 'vary':
            found_vary = True
            if 'accept' not in VARY_SEPARATOR.split(v.strip().lower()):
                v = v + ',Accept'
        if k.lower() == 'content-type':
            found_content_type = True
        fixed_headers.append((k, v))
    if not found_vary:
        fixed_headers.append(('Vary', 'Accept'))
    if not found_content_type:
        fixed_headers.append(('Content-Type', content_type))
    return fixed_headers

class MimeRenderBase(object):

    def __init__(self, global_default=None, global_override_arg_idx=None,
            global_override_input_key=None, global_charset=None,
            global_not_acceptable_callback=None):
        self.global_default = global_default
        self.global_override_arg_idx = global_override_arg_idx
        self.global_override_input_key = global_override_input_key
        self.global_charset = global_charset
        self.global_not_acceptable_callback = global_not_acceptable_callback

    def __call__(self, default=None, override_arg_idx=None,
            override_input_key=None, charset=None,
            not_acceptable_callback=None,
            **renderers):
        """
        Main mimerender decorator. Usage::

            @mimerender(default='xml', override_arg_idx=-1, override_input_key='format', , <renderers>)
            GET(self, ...) (or POST, etc.)
            
        The decorated function must return a dict with the objects necessary to
        render the final result to the user. The selected renderer will be 
        called with the dict contents as keyword arguments.
        If override_arg_idx isn't None, the wrapped function's positional
        argument at that index will be used instead of the Accept header.
        override_input_key works the same way, but with web.input().
        
        Example::

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
        if not override_arg_idx:
            override_arg_idx = self.global_override_arg_idx
        if not override_input_key:
            override_input_key = self.global_override_input_key
        if not charset: charset = self.global_charset
        if not not_acceptable_callback:
            not_acceptable_callback = self.global_not_acceptable_callback
        
        supported = list()
        renderer_dict = dict()
        for shortname, renderer in renderers.items():
            for mime in _get_mime_types(shortname):
                supported.append(mime)
                renderer_dict[mime] = renderer
        if default:
            default_mimes = _get_mime_types(default)
            # default mime types should be last in the supported list
            # (which means highest priority to mimeparse)
            for mime in reversed(default_mimes):
                supported.remove(mime)
                supported.append(mime)
            default_mime = default_mimes[0]
            default_renderer = get_renderer(default_mime)
        else:
            default_mime, default_renderer = next(iter(renderer_dict.items()))
        
        def wrap(target):
            @wraps(target)
            def wrapper(*args, **kwargs):
                self.target_args   = args
                self.target_kwargs = kwargs
                mime = None
                shortmime = None
                if override_arg_idx != None:
                    shortmime = args[override_arg_idx]
                if not shortmime and override_input_key:
                    shortmime = self._get_request_parameter(override_input_key)
                if shortmime: mime = _get_mime_types(shortmime)[0]
                accept_header = self._get_accept_header()
                if not mime:
                    if accept_header:
                        mime = _best_mime(supported, accept_header)
                    else:
                        mime = default_mime
                if mime:
                    renderer = get_renderer(mime)
                else:
                    if not_acceptable_callback:
                        content_type, entity = not_acceptable_callback(
                                accept_header, supported)
                        return self._make_response(entity,
                                                   (('Content-Type',
                                                     content_type),),
                                                   '406 Not Acceptable')
                    else:
                        mime, renderer = default_mime, default_renderer
                if not shortmime: shortmime = _get_short_mime(mime)
                context_vars = dict(
                        mimerender_shortmime=shortmime,
                        mimerender_mime=mime,
                        mimerender_renderer=renderer)
                for key, value in context_vars.items():
                    self._set_context_var(key, value)
                try:
                    result = target(*args, **kwargs)
                finally:
                    for key in context_vars.keys():
                        self._clear_context_var(key)
                content_type = mime
                if charset: content_type += '; charset=%s' % charset
                headers = ()
                status = '200 OK'
                if isinstance(result, tuple):
                    if len(result) == 3:
                        result, status, headers = result
                        try:
                            headers = headers.items()
                        except AttributeError:
                            pass
                    elif len(result) == 2:
                        result, status = result
                    elif len(result) == 1:
                        (result,) = result
                    else:
                        raise ValueError()
                content = renderer(**result)
                headers = _fix_headers(headers, content_type)
                return self._make_response(content, headers, status)
            if hasattr(wrapper, '__wrapped__'):
                # Workaround for new @wraps behavior in Python 3.4.
                # Prevents `TypeError: () got an unexpected keyword argument`
                # as reported in issue #25
                del wrapper.__wrapped__
            return wrapper
        
        return wrap
    
    def map_exceptions(self, mapping, *args, **kwargs):
        """
        Exception mapping helper decorator. Takes the same arguments as the
        main decorator, plus `mapping`, which is a list of 
        `(exception_class, status_line)` pairs.
        """
        @self.__call__(*args, **kwargs)
        def helper(e, status):
            return dict(exception=e), status

        def wrap(target):
            @wraps(target)
            def wrapper(*args, **kwargs):
                try:
                    return target(*args, **kwargs)
                except BaseException as e:
                    for klass, status in mapping:
                        if isinstance(e, klass):
                            return helper(e, status)
                    raise
            return wrapper
        return wrap

    def _get_request_parameter(self, key, default=None):
        return default

    def _get_accept_header(self, default=None):
        return default

    def _set_context_var(self, key, value):
        pass

    def _clear_context_var(self, key):
        pass

    def _make_response(self, content, headers, status):
        return content

# web.py implementation
try:
    import web
    class WebPyMimeRender(MimeRenderBase):
        def _get_request_parameter(self, key, default=None):
            return web.input().get(key, default)

        def _get_accept_header(self, default=None):
            return web.ctx.env.get('HTTP_ACCEPT', default)

        def _set_context_var(self, key, value):
            web.ctx[key] = value

        def _clear_context_var(self, key):
            del web.ctx[key]

        def _make_response(self, content, headers, status):
            web.ctx.status = status
            for k, v in headers:
                web.header(k, v)
            return content

except ImportError:
    pass

# Flask implementation
try:
    import flask
    class FlaskMimeRender(MimeRenderBase):
        def _get_request_parameter(self, key, default=None):
            return flask.request.values.get(key, default)

        def _get_accept_header(self, default=None):
            return flask.request.headers.get('Accept', default)

        def _set_context_var(self, key, value):
            flask.request.environ[key] = value

        def _clear_context_var(self, key):
            del flask.request.environ[key]

        def _make_response(self, content, headers, status):
            return flask.make_response(content, status, headers)

except ImportError:
    pass

# Bottle implementation
try:
    import bottle
    class BottleMimeRender(MimeRenderBase):
        def _get_request_parameter(self, key, default=None):
            return bottle.request.params.get(key, default)

        def _get_accept_header(self, default=None):
            return bottle.request.headers.get('Accept', default)

        def _set_context_var(self, key, value):
            bottle.request.environ[key] = value

        def _clear_context_var(self, key):
            del bottle.request.environ[key]

        def _make_response(self, content, headers, status):
            bottle.response.status = status
            for k, v in headers:
                bottle.response.headers[k] = v
            return content

except ImportError:
    pass

# webapp2 implementation
try:
    import webapp2
    class Webapp2MimeRender(MimeRenderBase):
        def _get_request_parameter(self, key, default=None):
            return webapp2.get_request().get(key, default_value=default)

        def _get_accept_header(self, default=None):
            return webapp2.get_request().headers.get('Accept', default)

        def _set_context_var(self, key, value):
            setattr(webapp2.get_request(), key, value)

        def _clear_context_var(self, key):
            delattr(webapp2.get_request(), key)

        def _make_response(self, content, headers, status):
            response = webapp2.get_request().response
            response.status = status
            for k, v in headers:
                response.headers[k] = v
            response.write(content)

except ImportError:
    pass

def wsgi_wrap(app):
    '''
    Wraps a standard wsgi application e.g.:
        def app(environ, start_response)
    It intercepts the start_response callback and grabs the results from it
    so it can return the status, headers, and body as a tuple
    '''
    @wraps(app)
    def wrapped(environ, start_response):
        status_headers = [None, None]
        def _start_response(status, headers):
            status_headers[:] = [status, headers]
        body = app(environ, _start_response)
        ret = body, status_headers[0], status_headers[1]
        return ret
    return wrapped

class _WSGIMimeRender(MimeRenderBase):
    def _get_request_parameter(self, key, default=None):
        environ, start_response = self.target_args
        return environ.get(key, default)

    def _get_accept_header(self, default=None):
        environ, start_response = self.target_args
        return environ.get('HTTP_ACCEPT', default)

    def _set_context_var(self, key, value):
        environ, start_response = self.target_args
        environ[key] = value

    def _clear_context_var(self, key):
        environ, start_response = self.target_args
        del environ[key]

    def _make_response(self, content, headers, status):
        environ, start_response = self.target_args
        start_response(status, headers)
        return content


def WSGIMimeRender(*args, **kwargs):
    '''
    A wrapper for _WSGIMimeRender that wrapps the
    inner callable with wsgi_wrap first.
    '''
    def wrapper(*args2, **kwargs2):
        # take the function
        def wrapped(f):
            return _WSGIMimeRender(*args, **kwargs)(*args2, **kwargs2)(wsgi_wrap(f))
        return wrapped
    return wrapper

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
            self.headers = {}

        def _get_request_parameter(self, key, default=None):
            return self.request_parameters.get(key, default)

        def _get_accept_header(self, default=None):
            return self.accept_header

        def _set_context_var(self, key, value):
            self.ctx[key] = value

        def _clear_context_var(self, key):
            del self.ctx[key]

        def _make_response(self, content, headers, status):
            self.status = status
            for k, v in headers:
                self.headers[k] = v
            return content

    class MimeRenderTests(unittest.TestCase):
        def test_single_variant(self):
            mimerender = TestMimeRender()
            result = mimerender(
                    xml=lambda x: '<xml>%s</xml>' % x
                    )(lambda: dict(x='test'))()
            self.assertEqual(mimerender.headers['Content-Type'], 'text/xml')
            self.assertEqual(result, '<xml>test</xml>')

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
            self.assertEqual(mimerender.headers['Content-Type'], 'text/plain')
            self.assertEqual(result, 'txt:default')

            mimerender.accept_header = 'application/xml'
            result = handler('a')
            self.assertEqual(mimerender.headers['Content-Type'], 'application/xml')
            self.assertEqual(result, 'xml:a')

            mimerender.accept_header = 'application/json'
            result = handler('b')
            self.assertEqual(mimerender.headers['Content-Type'], 'application/json')
            self.assertEqual(result, 'json:b')

            mimerender.request_parameters['mime'] = 'html'
            result = handler('c')
            self.assertEqual(mimerender.headers['Content-Type'], 'text/html')
            self.assertEqual(result, 'html:c')

        def test_default_for_wildcard_query(self):
            mimerender = TestMimeRender()
            mimerender.accept_header = '*/*'
            mimerender(
                    default='xml',
                    txt=lambda: None,
                    xml=lambda: None)(lambda: {})()
            self.assertEqual(mimerender.headers['Content-Type'], _MIME_TYPES['xml'][0])
            mimerender(
                    default='txt',
                    txt=lambda: None,
                    xml=lambda: None)(lambda: {})()
            self.assertEqual(mimerender.headers['Content-Type'], _MIME_TYPES['txt'][0])

        def test_decorated_function_name(self):
            def vanilla_function(): pass
            mimerender = TestMimeRender()
            decorated_function = mimerender(xml=None)(vanilla_function)
            self.assertEqual(vanilla_function.__name__,
                    decorated_function.__name__)

        def test_not_acceptable(self):
            mimerender = TestMimeRender()
            # default behavior, pick default even if not acceptable
            handler = mimerender(
                    default='json',
                    xml=lambda x: 'xml:%s' %x,
                    json=lambda x: 'json:%s' %x,
                    )(lambda x: dict(x=x))
            mimerender.accept_header = 'text/plain'
            result = handler('default')
            self.assertEqual(mimerender.headers['Content-Type'], 'application/json')
            self.assertEqual(mimerender.status, '200 OK')
            self.assertEqual(result, 'json:default')
            # optional: fail with 406
            handler = mimerender(
                    not_acceptable_callback= lambda _, sup: (
                        'text/plain',
                        'Available Content Types: ' + ', '.join(sup)),
                    default='json',
                    xml=lambda x: 'xml:%s' %x,
                    json=lambda x: 'json:%s' %x,
                    )(lambda x: dict(x=x))
            mimerender.accept_header = 'text/plain'
            result = handler('default')
            self.assertEqual(mimerender.headers['Content-Type'], 'text/plain')
            self.assertEqual(mimerender.status, '406 Not Acceptable')
            self.assertTrue(result.startswith('Available Content Types: '))
            self.assertTrue(result.find('application/xml') != -1)
            self.assertTrue(result.find('application/json') != -1)

        def test_map_exceptions(self):
            class MyException1(Exception): pass
            class MyException2(MyException1): pass
            def failifnone(x, exception_class=Exception):
                if x is None:
                    raise exception_class('info', 'moreinfo')
                return dict(x=x)
            mimerender = TestMimeRender()
            handler = mimerender.map_exceptions(
                    mapping=((MyException2, '500 Crazy Internal Error'),
                        (MyException1, '400 Failed')),
                    default='txt',
                    txt=lambda exception: 'txt:%s' % exception,
                    xml=lambda exception: 'xml:%s' % exception,
                    )(mimerender(
                    default='txt',
                    txt=lambda x: 'txt:%s' %x,
                    xml=lambda x: 'xml:%s' % x,
                    )(failifnone))

            # no exception thrown means normal mimerender behavior
            mimerender.accept_header = 'application/xml'
            result = handler('a')
            self.assertEqual(mimerender.status, '200 OK')
            self.assertEqual(mimerender.headers['Content-Type'], 'application/xml')
            self.assertEqual(result, 'xml:a')

            mimerender.accept_header = 'text/plain'
            result = handler('b')
            self.assertEqual(mimerender.headers['Content-Type'], 'text/plain')
            self.assertEqual(mimerender.status, '200 OK')
            self.assertEqual(result, 'txt:b')
    
            # unmapped exception won't be caught
            try:
                result = handler(None, Exception)
                self.fail('unmapped exception must not be caught')
            except:
                pass

            # mapped exceptions are represented with an acceptable mime type
            mimerender.accept_header = 'application/xml'
            result = handler(None, MyException1)
            self.assertEqual(mimerender.headers['Content-Type'], 'application/xml')
            self.assertNotEqual(mimerender.status, '200 OK')
            self.assertEqual(result, "xml:('info', 'moreinfo')")

            mimerender.accept_header = 'text/plain'
            result = handler(None, MyException1)
            self.assertEqual(mimerender.headers['Content-Type'], 'text/plain')
            self.assertNotEqual(mimerender.status, '200 OK')
            self.assertEqual(result, "txt:('info', 'moreinfo')")

            # mapping order matters over exception hierarchies
            result = handler(None, MyException2)
            self.assertEqual(mimerender.status, '500 Crazy Internal Error')

            result = handler(None, MyException1)
            self.assertEqual(mimerender.status, '400 Failed')

        def test_vary_header(self):
            mimerender = TestMimeRender()
            # add vary header if absent
            mimerender(xml=lambda: None)(lambda: {})()
            self.assertEqual(mimerender.headers['Vary'], 'Accept')
            # leave vary header untouched if accept is already there
            mimerender(xml=lambda: None)(
                lambda: ({}, '', (('Vary', 'Accept,X'),)))()
            self.assertEqual(mimerender.headers['Vary'], 'Accept,X')
            # append accept if vary header is incomplete
            mimerender(xml=lambda: None)(
                lambda: ({}, '', (('Vary', 'X'),)))()
            self.assertEqual(mimerender.headers['Vary'], 'X,Accept')

        def test_response_types(self):
            mimerender = TestMimeRender()
            # dict only
            mimerender(xml=lambda: None)(lambda: {})()
            self.assertEqual(mimerender.status, '200 OK')
            self.assertEqual(mimerender.headers, {'Vary': 'Accept',
                                                  'Content-Type': 'text/xml'})
            # dict + status
            mimerender(xml=lambda: None)(lambda: ({}, '666 Armaggedon'))()
            self.assertEqual(mimerender.status, '666 Armaggedon')
            self.assertEqual(mimerender.headers, {'Vary': 'Accept',
                                                  'Content-Type': 'text/xml'})
            # dict + status + headers
            mimerender(xml=lambda: None)(lambda: ({}, '666 Armaggedon',
                                                  {'X-Y': 'Z'}))()
            self.assertEqual(mimerender.status, '666 Armaggedon')
            self.assertEqual(mimerender.headers, {'Vary': 'Accept',
                                                  'Content-Type': 'text/xml',
                                                  'X-Y': 'Z'})

    
    unittest.main()
