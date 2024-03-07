# Development

This guide is intended to be used by contributors looking to make changes to the Linode CLI.

## Overview

The following section outlines the core functions of the Linode CLI.

### OpenAPI Specification Parsing

Most Linode CLI commands (excluding [plugin commands](https://github.com/linode/linode-cli/tree/dev/linodecli/plugins)) 
are generated dynamically at build-time from the [Linode OpenAPI Specification](https://github.com/linode/linode-api-docs),
which is also used to generate the [official Linode API documentation](https://www.linode.com/docs/api/). 

Each OpenAPI spec endpoint method is parsed into an `OpenAPIOperation` object. 
This object includes all necessary request and response arguments to create a command, 
stored as `OpenAPIRequestArg` and `OpenAPIResponseAttr` objects respectively. 
At runtime, the Linode CLI changes each `OpenAPIRequestArg` to an argparse argument and 
each `OpenAPIResponseAttr` to an outputtable column. It can also manage complex structures like 
nested objects and lists, resulting in commands and outputs that may not 
exactly match the OpenAPI specification.

### Baking

The "baking" process is run with `make bake`, `make install`, and `make build` targets, 
wrapping the `linode-cli bake` command.

Objects representing each command are serialized into the `data-3` file via the [pickle](https://docs.python.org/3/library/pickle.html) 
package, and are included in release artifacts as a [data file](https://setuptools.pypa.io/en/latest/userguide/datafiles.html). 
This enables quick command loading at runtime and eliminates the need for runtime parsing logic.

### Configuration

The Linode CLI can be configured using the `linode-cli configure` command, which allows users to
configure the following:

- A Linode API token
  - This can optionally be done using OAuth, see [OAuth Authentication](#oauth-authentication)
- Default values for commonly used fields (e.g. region, image)
- Overrides for the target API URL (hostname, version, scheme, etc.)

This command serves as an interactive prompt and outputs a configuration file to `~/.config/linode-cli`.
This file is in a simple INI format and can be easily modified manually by users.

Additionally, multiple users can be created for the CLI which can be designated when running commands using the `--as-user` argument
or using the `default-user` config variable.

When running a command, the config file is loaded into a `CLIConfig` object stored under the `CLI.config` field. 
This object allows various parts of the CLI to access the current user, the configured token, and any other CLI config values by name.

The logic for the interactive prompt and the logic for storing the CLI configuration can be found in the
`configuration` package. 

### OAuth Authentication

In addition to allowing users to configure a token manually, they can automatically generate a CLI token under their account using
an OAuth workflow. This workflow uses the [Linode OAuth API](https://www.linode.com/docs/api/#oauth) to generate a temporary token,
which is then used to generate a long-term token stored in the CLI config file.

The OAuth client ID is hardcoded and references a client under an officially managed Linode account.

All the logic for OAuth token generation is stored in the `configuration/auth.py` file.


