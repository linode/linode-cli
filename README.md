# linode-cli (lin)

The Linode Command Line Interface

Provides easy access to any of the Linode API endpoints from the command line and displays results in an organized, configurable table. 

This project is automatically generated from the [Linode OpenAPI spec](https://www.linode.com/docs/api/) using the [openapi3 Python package](https://github.com/Dorthu/openapi3).

![Example of CLI in use](https://raw.githubusercontent.com/linode/linode-cli/main/demo.gif)

Visit the [Wiki](../../wiki) for more information.

## Install

We recommend installing `linode-cli` with `pipx`, which installs each Python CLI tool into its own isolated environment and works on distributions where `pip install` fails because the system Python is marked as externally managed ([PEP 668](https://peps.python.org/pep-0668/)). If pipx isn't installed yet, follow the [pipx installation guide](https://pipx.pypa.io/latest/how-to/install-pipx.html).

To install:

```bash
pipx install linode-cli
```

To upgrade:

```bash
pipx upgrade linode-cli
```

The [Wiki](https://github.com/linode/linode-cli/wiki/Installation) covers other installation methods, including the Docker image, the GitHub Action, and building from source.

## Contributing

This CLI is generated from the [OpenAPI specification for Linode's API](https://github.com/linode/linode-api-openapi).  As
such, many changes are made directly to the spec.

Please follow the [Contributing Guidelines](https://github.com/linode/linode-cli/blob/main/CONTRIBUTING.md) when making a contribution.
