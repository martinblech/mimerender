#!/usr/bin/env python

from setuptools import setup

setup(
    name='mimerender',
    version='0.5.1',
    description='RESTful HTTP Content Negotiation for Flask, Bottle, web.py '
        'and webapp2 (Google App Engine)',
    author='Martin Blech',
    author_email='martinblech@gmail.com',
    url='https://github.com/martinblech/mimerender',
    license='MIT',
    long_description="""This module provides a decorator that wraps a HTTP
    request handler to select the correct render function for a given HTTP
    Accept header. It uses mimeparse to parse the accept string and select the
    best available representation. Supports Flask, Bottle, web.py and webapp2
    out of the box, and it's easy to add support for other frameworks.""",
    platforms=['all'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    py_modules=['mimerender'],
    package_dir={'':'src'},
    requires=['python_mimeparse (>=0.1.4)'],
    install_requires=['python_mimeparse >= 0.1.4'],
)
