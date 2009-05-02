#!/usr/bin/env python

from distutils.core import setup

setup(
    name='mimerender',
    version='0.1',
    description='RESTful resource variant rendering using MIME Media-Types',
    author='Martin Blech',
    author_email='mblech@bmat.com',
    url='http://code.google.com/p/mimerender/',
    py_modules=['mimerender'],
    package_dir={'':'src'},
    requires=['mimeparse', 'web.py (>=0.3)'],
)
