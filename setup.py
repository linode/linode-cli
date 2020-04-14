#!/usr/bin/env python3
from io import open
from setuptools import setup
from os import path
import subprocess


here = path.abspath(path.dirname(__file__))


# get the long description from the README.rst
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


def get_baked_files():
    """
    A helper to retrieve the baked files included with this package.  This is
    to assist with building from source, where baked files may not be present
    on a fresh clone
    """
    data_files = []

    if path.isfile('linode-cli.sh'):
        data_files.append(('/etc/bash_completion.d', ['linode-cli.sh']))

    return data_files


def get_version():
    """
    Uses the version file to calculate this package's version
    """
    return subprocess.check_output(["./version"]).decode("utf-8").rstrip()


setup(
    name="linode-cli",
    version=get_version(),
    description="CLI for the Linode API",
    long_description=long_description,
    author="Linode",
    author_email='developers@linode.com',
    url="https://developers.linode.com/api/v4",
    packages=[
        'linodecli',
        'linodecli.plugins',
    ],
    license="BSD 3-Clause License",
    install_requires=[
        "terminaltables",
        "colorclass",
        "requests",
        "PyYAML",
        "enum34;python_version<'3.4'",
    ],
    entry_points={
        "console_scripts": [
            "linode-cli = linodecli:main",
        ]
    },
    data_files=get_baked_files(),
    python_requires=">=2.7",
    include_package_data=True
)
