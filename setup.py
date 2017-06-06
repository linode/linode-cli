#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="linode-cli",
    version="4.0.7a",
    description="CLI for Linode API v4",
    author="Linode",
    author_email="wsmith@linode.com",
    url="https://www.linode.com/docs/platform/linode-cli",
    packages=['linodecli','linodecli.resources'],
    install_requires=["linode-api","terminaltables","colorclass"],
    entry_points={
        "console_scripts": [ "linode-beta = linodecli.cli:main" ],
    },
    python_requires=">=3.4"
)
