# -*- coding: utf-8 -*-
"""
EspyMetrics is an example application created for the Enterprise
Software with Python course.
"""


from setuptools import setup, find_packages

NAME = 'espymetrics'
AUTHOR = 'Mahmoud Hashemi'
VERSION = '15.0'
CONTACT = 'mahmoud@hatnote.com'
URL = 'https://github.com/mahmoud/espymetrics'
LICENSE = 'BSD'

setup(
    name=NAME,
    version=VERSION,
    long_description=__doc__,
    author=AUTHOR,
    author_email=CONTACT,
    url=URL,
    packages=find_packages(),
    install_requires=['boltons>=16.2.0',
                      'clastic==0.4.3'],
    include_package_data=True,
    classifiers=['Intended Audience :: Developers',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7'])
