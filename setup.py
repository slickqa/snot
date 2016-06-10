#!/usr/bin/env python

__author__ = 'Jason Corbett'

from setuptools import setup, find_packages

setup(
    name="slickqa-snot",
    description="A plugin to nose to allow results from python tests to be put into slick.",
    version="1.0" + open("build.txt").read().strip(),
    license="License :: OSI Approved :: Apache Software License",
    long_description=open('README.txt').read(),
    py_modules=['snot'],
    #packages=find_packages(exclude=['distribute_setup']),
    #package_data={'': ['*.txt', '*.rst', '*.html']},
    #include_package_data=True,
    install_requires=['slickqa>=2.0.669', 'nose', 'docutils'],
    author="Slick Developers",
    url="http://github.com/slickqa/snot",
    entry_points={
        'nose.plugins.0.10': [
            'snot = snot:SlickAsSnotPlugin'
        ]
    }
)
