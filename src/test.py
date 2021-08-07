# -*- coding: utf-8 -*-
# unit tests
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mimerender
from mimerender import _MIME_TYPES


class TestMimeRender(mimerender.MimeRenderBase):
    __test__ = False

    def __init__(self, request_parameters=None, accept_header=None, *args, **kwargs):
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
    def test_single_variant_without_default(self):
        mimerender = TestMimeRender()
        result = mimerender(
            xml=lambda x: "<xml>%s</xml>" % x,
        )(lambda: dict(x="test"))()
        self.assertEqual(mimerender.headers["Content-Type"], "text/xml")
        self.assertEqual(result, "<xml>test</xml>")

    def test_single_variant_with_default(self):
        mimerender = TestMimeRender()
        result = mimerender(xml=lambda x: "<xml>%s</xml>" % x, default="xml")(
            lambda: dict(x="test")
        )()
        self.assertEqual(mimerender.headers["Content-Type"], "text/xml")
        self.assertEqual(result, "<xml>test</xml>")

    def test_norenderers(self):
        try:
            TestMimeRender()()
            self.fail("should fail with ValueError")
        except ValueError:
            pass

    def test_select_variant(self):
        mimerender = TestMimeRender()
        handler = mimerender(
            default="txt",
            override_input_key="mime",
            txt=lambda x: "txt:%s" % x,
            xml=lambda x: "xml:%s" % x,
            json=lambda x: "json:%s" % x,
            html=lambda x: "html:%s" % x,
        )(lambda x: dict(x=x))

        result = handler("default")
        self.assertEqual(mimerender.headers["Content-Type"], "text/plain")
        self.assertEqual(result, "txt:default")

        mimerender.accept_header = "application/xml"
        result = handler("a")
        self.assertEqual(mimerender.headers["Content-Type"], "application/xml")
        self.assertEqual(result, "xml:a")

        mimerender.accept_header = "application/json"
        result = handler("b")
        self.assertEqual(mimerender.headers["Content-Type"], "application/json")
        self.assertEqual(result, "json:b")

        mimerender.request_parameters["mime"] = "html"
        result = handler("c")
        self.assertEqual(mimerender.headers["Content-Type"], "text/html")
        self.assertEqual(result, "html:c")

    def test_default_for_wildcard_query(self):
        mimerender = TestMimeRender()
        mimerender.accept_header = "*/*"
        mimerender(default="xml", txt=lambda: None, xml=lambda: None)(lambda: {})()
        self.assertEqual(mimerender.headers["Content-Type"], _MIME_TYPES["xml"][0])
        mimerender(default="txt", txt=lambda: None, xml=lambda: None)(lambda: {})()
        self.assertEqual(mimerender.headers["Content-Type"], _MIME_TYPES["txt"][0])

    def test_decorated_function_name(self):
        def vanilla_function():
            pass

        mimerender = TestMimeRender()
        decorated_function = mimerender(xml=None)(vanilla_function)
        self.assertEqual(vanilla_function.__name__, decorated_function.__name__)

    def test_not_acceptable(self):
        mimerender = TestMimeRender()
        # default behavior, pick default even if not acceptable
        handler = mimerender(
            default="json",
            xml=lambda x: "xml:%s" % x,
            json=lambda x: "json:%s" % x,
        )(lambda x: dict(x=x))
        mimerender.accept_header = "text/plain"
        result = handler("default")
        self.assertEqual(mimerender.headers["Content-Type"], "application/json")
        self.assertEqual(mimerender.status, "200 OK")
        self.assertEqual(result, "json:default")
        # optional: fail with 406
        handler = mimerender(
            not_acceptable_callback=lambda _, sup: (
                "text/plain",
                "Available Content Types: " + ", ".join(sup),
            ),
            default="json",
            xml=lambda x: "xml:%s" % x,
            json=lambda x: "json:%s" % x,
        )(lambda x: dict(x=x))
        mimerender.accept_header = "text/plain"
        result = handler("default")
        self.assertEqual(mimerender.headers["Content-Type"], "text/plain")
        self.assertEqual(mimerender.status, "406 Not Acceptable")
        self.assertTrue(result.startswith("Available Content Types: "))
        self.assertTrue(result.find("application/xml") != -1)
        self.assertTrue(result.find("application/json") != -1)

    def test_map_exceptions(self):
        class MyException1(Exception):
            pass

        class MyException2(MyException1):
            pass

        def failifnone(x, exception_class=Exception):
            if x is None:
                raise exception_class("info", "moreinfo")
            return dict(x=x)

        mimerender = TestMimeRender()
        handler = mimerender.map_exceptions(
            mapping=(
                (MyException2, "500 Crazy Internal Error"),
                (MyException1, "400 Failed"),
            ),
            default="txt",
            txt=lambda exception: "txt:%s" % exception,
            xml=lambda exception: "xml:%s" % exception,
        )(
            mimerender(
                default="txt",
                txt=lambda x: "txt:%s" % x,
                xml=lambda x: "xml:%s" % x,
            )(failifnone)
        )

        # no exception thrown means normal mimerender behavior
        mimerender.accept_header = "application/xml"
        result = handler("a")
        self.assertEqual(mimerender.status, "200 OK")
        self.assertEqual(mimerender.headers["Content-Type"], "application/xml")
        self.assertEqual(result, "xml:a")

        mimerender.accept_header = "text/plain"
        result = handler("b")
        self.assertEqual(mimerender.headers["Content-Type"], "text/plain")
        self.assertEqual(mimerender.status, "200 OK")
        self.assertEqual(result, "txt:b")

        # unmapped exception won't be caught
        try:
            result = handler(None, Exception)
            self.fail("unmapped exception must not be caught")
        except Exception:
            pass

        # mapped exceptions are represented with an acceptable mime type
        mimerender.accept_header = "application/xml"
        result = handler(None, MyException1)
        self.assertEqual(mimerender.headers["Content-Type"], "application/xml")
        self.assertNotEqual(mimerender.status, "200 OK")
        self.assertEqual(result, "xml:('info', 'moreinfo')")

        mimerender.accept_header = "text/plain"
        result = handler(None, MyException1)
        self.assertEqual(mimerender.headers["Content-Type"], "text/plain")
        self.assertNotEqual(mimerender.status, "200 OK")
        self.assertEqual(result, "txt:('info', 'moreinfo')")

        # mapping order matters over exception hierarchies
        result = handler(None, MyException2)
        self.assertEqual(mimerender.status, "500 Crazy Internal Error")

        result = handler(None, MyException1)
        self.assertEqual(mimerender.status, "400 Failed")

    def test_vary_header(self):
        mimerender = TestMimeRender()
        # add vary header if absent
        mimerender(xml=lambda: None)(lambda: {})()
        self.assertEqual(mimerender.headers["Vary"], "Accept")
        # leave vary header untouched if accept is already there
        mimerender(xml=lambda: None)(lambda: ({}, "", (("Vary", "Accept,X"),)))()
        self.assertEqual(mimerender.headers["Vary"], "Accept,X")
        # append accept if vary header is incomplete
        mimerender(xml=lambda: None)(lambda: ({}, "", (("Vary", "X"),)))()
        self.assertEqual(mimerender.headers["Vary"], "X,Accept")

    def test_response_types(self):
        mimerender = TestMimeRender()
        # dict only
        mimerender(xml=lambda: None)(lambda: {})()
        self.assertEqual(mimerender.status, "200 OK")
        self.assertEqual(
            mimerender.headers, {"Vary": "Accept", "Content-Type": "text/xml"}
        )
        # dict + status
        mimerender(xml=lambda: None)(lambda: ({}, "666 Armaggedon"))()
        self.assertEqual(mimerender.status, "666 Armaggedon")
        self.assertEqual(
            mimerender.headers, {"Vary": "Accept", "Content-Type": "text/xml"}
        )
        # dict + status + headers
        mimerender(xml=lambda: None)(lambda: ({}, "666 Armaggedon", {"X-Y": "Z"}))()
        self.assertEqual(mimerender.status, "666 Armaggedon")
        self.assertEqual(
            mimerender.headers,
            {"Vary": "Accept", "Content-Type": "text/xml", "X-Y": "Z"},
        )

    def test_invalid_accept_header(self):
        mimerender = TestMimeRender()
        # default behavior, pick default even if not acceptable
        handler = mimerender(
            default="json",
            xml=lambda x: "xml:%s" % x,
            json=lambda x: "json:%s" % x,
        )(lambda x: dict(x=x))
        mimerender.accept_header = "text"  # invalid header
        result = handler("default")
        self.assertEqual(mimerender.headers["Content-Type"], "text/plain")
        self.assertEqual(mimerender.status, "400 Bad Request")
        self.assertEqual(result, "Invalid Accept header requested")


if __name__ == "__main__":
    unittest.main()
