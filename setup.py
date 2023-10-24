#!/usr/bin/env python3
import pathlib
import subprocess
import sys
import platform

from setuptools import setup, find_packages
from os import path

here = pathlib.Path().absolute()


# get the long description from the README.md
with open(here / "README.md", encoding="utf-8") as f:
    long_description = f.read()


def get_baked_files():
    """
    A helper to retrieve the baked files included with this package.  This is
    to assist with building from source, where baked files may not be present
    on a fresh clone
    """
    data_files = []

    completion_dir = "/etc/bash_completion.d"

    if path.isfile("linode-cli.sh") and platform.system() != "Windows":
        data_files.append((completion_dir, ["linode-cli.sh"]))

    return data_files


def get_version():
    """
    Uses the version file to calculate this package's version
    """
    return (
        subprocess.check_output([sys.executable, "./version"])
        .decode("utf-8")
        .rstrip()
    )


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

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="linode-cli",
    version=version,
    description="CLI for the Linode API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Linode",
    author_email="developers@linode.com",
    url="https://www.linode.com/docs/api/",
    packages=find_packages(include=["linodecli*"]),
    license="BSD 3-Clause License",
    install_requires=requirements,
    extras_require={
        "obj": ["boto3"],
    },
    entry_points={
        "console_scripts": [
            "linode-cli = linodecli:main",
            "linode = linodecli:main",
            "lin  = linodecli:main",
        ]
    },
    data_files=get_baked_files(),
    python_requires=">=3.8",
    include_package_data=True,
)
