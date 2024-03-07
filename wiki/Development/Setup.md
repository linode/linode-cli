# Linode CLI Development Setup Guide

The following guide outlines to the process for setting up the Linode CLI for development.

## Cloning the Repository

The Linode CLI repository can be cloned locally using the following command:

```bash
git clone git@github.com:linode/linode-cli.git
```

If you do not have an SSH key configured, you can alternatively use the following command:

```bash
git clone https://github.com/linode/linode-cli.git
```

## Configuring a VirtualEnv (recommended)

A virtual env allows you to create virtual Python environment which can prevent potential 
Python dependency conflicts.

To create a VirtualEnv, run the following:

```bash
python3 -m venv .venv
```

To enter the VirtualEnv, run the following command (NOTE: This needs to be run every time you open your shell):

```bash
source .venv/bin/activate
```

## Installing Project Dependencies

All Linode CLI Python requirements be installed by running the following command:

```bash
make requirements
```

## Building and Installing the Project

The Linode CLI can be built and installed using the `make install` target:

```bash
make install
```

Alternatively you can build but not install the CLI using the `make build` target:

```bash
make build
```

Optionally you can validate that you have installed a local version of the CLI using the `linode-cli --version` command:

```bash
linode-cli --version

# Output:
# linode-cli 0.0.0
# Built off spec version 4.173.0
#
# The 0.0.0 implies this is a locally built version of the CLI
```

## Building Using a Custom OpenAPI Specification

In some cases, you may want to build the CLI using a custom or modified OpenAPI specification.

This can be achieved using the `SPEC` Makefile argument, for example:

```bash
# Download the OpenAPI spec
curl -o openapi.yaml https://raw.githubusercontent.com/linode/linode-api-docs/development/openapi.yaml

# Many arbitrary changes to the spec

# Build & install the CLI using the modified spec
make SPEC=$PWD/openapi.yaml install
```

## Next Steps

To continue to the next step of this guide, continue to the [Testing page](./Testing.md).