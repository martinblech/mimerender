#!/usr/bin/env python

from setuptools import setup

setup(
    name='mimerender',
    version='0.3.1',
    description='RESTful resource variant selection using the '
        'HTTP Accept header',
    author='Martin Blech',
    author_email='martinblech@gmail.com',
    url='https://github.com/martinblech/mimerender',
    license='MIT',
    long_description="""This module provides a decorator that wraps a HTTP
    request handler to select the correct render function for a given HTTP
    Accept header. It uses mimeparse to parse the accept string and select the
    best available representation.""",
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
