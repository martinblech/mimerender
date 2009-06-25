#!/usr/bin/env python

from distutils.core import setup

setup(
    name='mimerender',
    version='0.2.2',
    description='RESTful resource variant rendering using MIME Media-Types',
    author='Martin Blech',
    author_email='mblech@bmat.com',
    url='http://code.google.com/p/mimerender/',
    license='MIT',
    long_description="""
    This module allows, with the use of python decorators, to transparently select a render function for an HTTP request handler's result. It uses mimeparse to parse the HTTP Accept header and select the best available representation. Currently it only supports (web.py), but other web frameworks can be considered.
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
    requires=['mimeparse', 'web.py'],
    install_requires=['mimeparse', 'web.py'],
)
