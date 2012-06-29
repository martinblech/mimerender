mimerender's documentation
==========================

mimerender is a Python module for RESTful resource variant selection using the HTTP Accept header

It acts as a decorator that wraps a HTTP request handler to select the correct render function for a given HTTP Accept header. It uses `mimeparse <http://code.google.com/p/mimeparse>`_ to parse the accept string and select the best available representation.

Support for `webapp2 <http://webapp-improved.appspot.com/>`_ (`Google App Engine <https://developers.google.com/appengine/>`_), `web.py <http://webpy.org>`_, `Flask <http://flask.pocoo.org>`_ and `Bottle <http://bottlepy.org>`_ is available out of the box and it's easy to add support for your favourite framework, just extend the :class:`MimeRenderBase` class.

Contents
========

.. toctree::
    :maxdepth: 2

    examples
    api



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

