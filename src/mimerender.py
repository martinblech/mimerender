"""
Decorator for RESTful resource variant selection in web.py.
"""

__version__   = '0.2.3'
__author__    = 'Martin Blech <mblech@bmat.com>'
__license__   = 'MIT'
__copyright__ = '2009 Barcelona Music & Audio Technologies'

import threading
import web
import mimeparse

ctx = web.threadeddict()

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

class MimeRenderException(Exception): pass

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

def _best_mime(supported, accept_string = None):
    try:
        if accept_string == None: accept_string = web.ctx.env['HTTP_ACCEPT']
    except KeyError:
        return None
    return mimeparse.best_match(supported, accept_string)

global_default = None
global_override_arg_idx = None
global_override_input_key = None
global_charset = None

def mimerender(default=None, override_arg_idx=None, override_input_key=None,
               charset=None, **renderers):
    """
    Usage:
        @mimerender(default='xml', override_arg_idx=-1, override_input_key='format', , <renderers>)
        GET(self, ...) (or POST, etc.)
        
    The decorated function must return a dict with the objects necessary to
    render the final result to the user. The selected renderer will be called
    with the map contents as keyword arguments.
    If override_arg_idx isn't None, the wrapped function's positional argument
    at that index will be removed and used instead of the Accept header.
    override_input_key works the same way, but with web.input().
    
    Example:
    class greet:
        @mimerender.mimerender(
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
        def GET(self, param):
            message = 'Hello, %s!'%param
            return {'message':message}
    """
    def get_renderer(mime):
        try:
            return renderer_dict[mime]
        except KeyError:
            raise MimeRenderException('No renderer for mime "%s"'%mime)
    
    if not default: default = global_default
    if not override_arg_idx: override_arg_idx = global_override_arg_idx
    if not override_input_key: override_input_key = global_override_input_key
    if not charset: charset = global_charset
    
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
                shortmime = web.input().get(override_input_key, None)
            if shortmime: mime = _get_mime_types(shortmime)[0]
            if not mime:
                mime = _best_mime(supported)
            if mime:
                renderer = get_renderer(mime)
            else:
                mime, renderer = default_mime, default_renderer
            if not shortmime: shortmime = _get_short_mime(mime)
            ctx.shortmime = shortmime
            ctx.mime = mime
            ctx.renderer = renderer
            result = target(*args, **kwargs)
            del ctx.renderer
            del ctx.mime
            del ctx.shortmime
            content_type = mime
            if charset: content_type += '; charset=%s' % charset
            web.header('Content-Type', content_type)
            return renderer(**result)
        return wrapper
    
    return wrap

if __name__ == "__main__":
    import unittest

    class TestMimeRender(unittest.TestCase):
        pass
    
    unittest.main()
