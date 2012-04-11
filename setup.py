#!/usr/bin/env python

from setuptools import setup

setup(
    name='mimerender',
    version='0.3',
    description='RESTful resource variant selection using the '
        'HTTP Accept header',
    author='Martin Blech',
    author_email='martinblech@gmail.com',
    url='http://code.google.com/p/mimerender/',
    license='MIT',
    long_description="""
    This module provides a decorator that allows to transparently select a
    render function for an HTTP request handler's result. It uses mimeparse to
    parse the HTTP Accept header and select the best available representation.
    It supports web.py, Flask and Bottle out of the box and it's easy to add
    support for your favourite framework, just extend MimeRenderBase.
    """,
    platforms=['all'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    
    py_modules=['mimerender'],
    package_dir={'':'src'},
    requires=['mimeparse'],
    install_requires=['mimeparse'],
)
