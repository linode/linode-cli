#!/usr/bin/env python3

from setuptools import setup

setup(name="linode-next",
        version="4.0.7a",
        description="CLI for Linode API v4",
        author="William Smith",
        author_email="wsmith@linode.com",
        url="https://www.linode.com/docs/platform/linode-cli",
        scripts=["cli.py"],
        install_requires=["linode-api","terminaltables","colorclass"])
