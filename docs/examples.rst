Usage Examples
==============

Content-Type selection
----------------------

A few examples on how to use :mod:`mimerender` with the different supported frameworks. Any of these will behave this way:

.. literalinclude:: ../examples/bottle_example.py
  :language: bash
  :lines: 3-25

Bottle
++++++

.. literalinclude:: ../examples/bottle_example.py
  :lines: 28-

Flask
+++++

.. literalinclude:: ../examples/flask_example.py
  :lines: 28-

Webapp2
+++++++

.. literalinclude:: ../examples/webapp2_example.py
  :lines: 28-

web.py
++++++

.. literalinclude:: ../examples/webpy_example.py
  :lines: 28-

Content-Type selection plus Exception Mapping
---------------------------------------------

:mod:`mimerender` provides a helper decorator for mapping exceptions to HTTP Status Codes.

.. literalinclude:: ../examples/exception_mapping_example.py
  :lines: 47-

:mod:`mimerender` will take care of mapping :class:`ValueError` and :class:`NotFound` to the specified HTTP status codes, and it will serialize the exception with an acceptable Content-Type:

.. literalinclude:: ../examples/exception_mapping_example.py
  :language: bash
  :lines: 3-45
