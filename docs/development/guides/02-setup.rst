.. _development_setup:

Setup
=====

The following guide outlines to the process for setting up the Linode CLI for development.

Cloning the Repository
----------------------

The Linode CLI repository can be cloned locally using the following command::

    git clone git@github.com:linode/linode-cli.git

If you do not have an SSH key configured, you can alternatively use the following command::

    git clone https://github.com/linode/linode-cli.git

Configuring a VirtualEnv (recommended)
--------------------------------------

A virtual env allows you to create virtual Python environment which can prevent potential 
Python dependency conflicts.

To create a VirtualEnv, run the following::

    python3 -m venv .venv

To enter the VirtualEnv, run the following command (NOTE: This needs to be run every time you open your shell)::

    source .venv/bin/activate

Installing Project Dependencies
-------------------------------

All Linode CLI Python requirements can be installed by running the following command::

    make requirements

Building and Installing the Project
-----------------------------------

The Linode CLI can be built and installed using the :code:`make install` target::

    make install

Alternatively you can build but not install the CLI using the :code:`make build` target::

    make build

Optionally you can validate that you have installed a local version of the CLI using the :code:`linode-cli --version` command::

    linode-cli --version

    # Output:
    # linode-cli 0.0.0
    # Built from spec version 4.173.0
    #
    # The 0.0.0 implies this is a locally built version of the CLI

Building Using a Custom OpenAPI Specification
---------------------------------------------

In some cases, you may want to build the CLI using a custom or modified OpenAPI specification.

This can be achieved using the :code:`SPEC` Makefile argument, for example::

    # Download the OpenAPI spec
    curl -o openapi.yaml https://raw.githubusercontent.com/linode/linode-api-docs/development/openapi.yaml

    # Make arbitrary changes to the spec

    # Build & install the CLI using the modified spec
    make SPEC=$PWD/openapi.yaml install

.. rubric:: Next Steps

To continue to the next step of this guide, continue to the :ref:`Project Skeleton page <development_project_skeleton>`.