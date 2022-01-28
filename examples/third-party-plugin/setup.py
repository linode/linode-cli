"""
This file allows installation of this plugin as a python module.  See the docs
for setuptools for more information.
"""
from setuptools import setup

setup(
    # replace this with the module name you want your plugin to install as
    name="example_third_party_plugin",
    # replace with your plugin's version - use semantic versioning if possible
    version=1,
    # this is used in pip to show details about your plugin
    description="Example third party plugin for the Linode CLI",
    # replace these fields with information about yourself or your organization
    author="linode",
    author_email="developers@linode.com",
    # in this case, the plugin is a single file, so that file is listed here
    # replace with the name of your plugin file, or use ``packages=[]`` to list
    # whole python modules to include
    py_modules=[
        "example_third_party_plugin",
    ],
)
