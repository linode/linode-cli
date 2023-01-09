#!/usr/bin/env python3
import subprocess
from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))


# get the long description from the README.rst
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()


def get_baked_files():
    """
    A helper to retrieve the baked files included with this package.  This is
    to assist with building from source, where baked files may not be present
    on a fresh clone
    """
    data_files = []

    if path.isfile("linode-cli.sh"):
        data_files.append(("/etc/bash_completion.d", ["linode-cli.sh"]))

    return data_files


def get_version():
    """
    Uses the version file to calculate this package's version
    """
    return subprocess.check_output(["./version"]).decode("utf-8").rstrip()


def get_baked_version():
    """
    Attempts to read the version from the baked_version file
    """
    with open("./baked_version", "r", encoding="utf-8") as f:
        result = f.read()

    return result


def bake_version(v):
    """
    Writes the given version to the baked_version file
    """
    with open("./baked_version", "w", encoding="utf-8") as f:
        f.write(v)


# If there's already a baked version, use it rather than attempting
# to resolve the version from env.
# This is useful for installing from an SDist where the version
# cannot be dynamically resolved.
#
# NOTE: baked_version is deleted when running `make build` and `make install`,
# so it should always be recreated during the build process.
if path.isfile("baked_version"):
    version = get_baked_version()
else:
    # Otherwise, retrieve and bake the version as normal
    version = get_version()
    bake_version(version)

setup(
    name="linode-cli",
    version=version,
    description="CLI for the Linode API",
    long_description=long_description,
    author="Linode",
    author_email="developers@linode.com",
    url="https://www.linode.com/docs/api/",
    packages=[
        "linodecli",
        "linodecli.plugins",
    ],
    license="BSD 3-Clause License",
    install_requires=[
        "terminaltables",
        "requests",
        "PyYAML",
        "future; python_version <= '3.0.0'",
    ],
    extras_require={
        ":python_version<'3.4'": ["enum34"],
    },
    entry_points={
        "console_scripts": [
            "linode-cli = linodecli:main",
        ]
    },
    data_files=get_baked_files(),
    python_requires=">=3.6",
    include_package_data=True,
)
