#!/usr/bin/env python

import requests
from setuptools import setup

try:
    from packaging.version import parse
except ImportError:
    from pip._vendor.packaging.version import parse

__author__ = 'Jason Corbett'


def get_requirements(filename):
    with open(filename) as f:
        return f.readlines()


URL_PATTERN = 'https://pypi.python.org/pypi/{package}/json'


def get_version_and_bump(package, url_pattern=URL_PATTERN):
    """Return version of package on pypi.python.org using json."""
    req = requests.get(url_pattern.format(package=package))
    version = parse('0')
    if req.status_code == requests.codes.ok:
        j = req.json()
        releases = j.get('releases', [])
        for release in releases:
            ver = parse(release)
            if not ver.is_prerelease:
                version = max(version, ver)
    return "{}.{}.{}".format(version.release[0], version.release[1], version.release[2] + 1)


setup(
    name="slickqa-snot",
    description="A plugin to nose to allow results from python tests to be put into slick.",
    version=get_version_and_bump(package="slickqa-snot"),
    license="License :: OSI Approved :: Apache Software License",
    long_description=open('README.txt').read(),
    py_modules=['snot'],
    # packages=find_packages(exclude=['distribute_setup']),
    # package_data={'': ['*.txt', '*.rst', '*.html']},
    # include_package_data=True,
    install_requires=get_requirements('requirements.txt'),
    author="Slick Developers",
    url="http://github.com/slickqa/snot",
    entry_points={
        'nose.plugins.0.10': [
            'snot = snot:SlickAsSnotPlugin'
        ]
    }
)
