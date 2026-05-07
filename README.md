# linode-cli (lin)

The Linode Command Line Interface

Provides easy access to any of the Linode API endpoints from the command line and displays results in an organized, configurable table. 

This project is automatically generated from the [Linode OpenAPI spec](https://www.linode.com/docs/api/) using the [openapi3 Python package](https://github.com/Dorthu/openapi3).

![Example of CLI in use](https://raw.githubusercontent.com/linode/linode-cli/main/demo.gif)

Visit the [Wiki](../../wiki) for more information.

## Install

Install via PyPI:
```bash
pipx install linode-cli
```
To upgrade:
```
pipx upgrade linode-cli
```
We recommend using `pipx` to install `linode-cli`, as it installs Python CLI tools in isolated environments and avoids conflicts with system-managed Python packages (PEP 668).
Visit the [Wiki](../../wiki/Installation) for more information.

## Contributing

This CLI is generated from the [OpenAPI specification for Linode's API](https://github.com/linode/linode-api-openapi).  As
such, many changes are made directly to the spec.

Please follow the [Contributing Guidelines](https://github.com/linode/linode-cli/blob/main/CONTRIBUTING.md) when making a contribution.
