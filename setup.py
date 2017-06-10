#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="linode-cli",
    version="1.0.3b2",
    description="CLI for Linode API v4",
    long_description=long_description,
    author="Linode",
    author_email="wsmith@linode.com",
    url="https://www.linode.com/docs/platform/linode-cli",
    packages=['linodecli','linodecli.resources'],
    install_requires=["linode-api>=4.1.0b0","terminaltables","colorclass"],
    entry_points={
        "console_scripts": [ "linode-beta = linodecli.cli:main" ],
    },
    python_requires=">=3.4"
)
