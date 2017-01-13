# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#
"""
Package setup for krux-marathon-api
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from setuptools import setup, find_packages

from krux_marathon_api import VERSION

# URL to the repository on Github.
REPO_URL = 'https://github.com/krux/krux-marathon-api'
# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
# We use the version to construct the DOWNLOAD_URL.
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))


setup(
    name='krux-marathon-api',
    version=VERSION,
    author='Erin Willingham',
    author_email='ewillingham@salesforce.com',
    description='Krux Marathon API tool for ensuring Marathon App state.',
    url=REPO_URL,
    download_url=DOWNLOAD_URL,
    license='All Rights Reserved.',
    packages=find_packages(),
    # dependencies are named in requirements.pip
    install_requires=[],
    entry_points={
        'console_scripts': [
            'marathon-api = krux_marathon_api.cli:main',
        ],
    },
)
