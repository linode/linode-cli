.. _development_overview:

Overview
========

The following section outlines the core functions of the Linode CLI.

OpenAPI Specification Parsing
-----------------------------

Most Linode CLI commands (excluding `plugin commands <https://github.com/linode/linode-cli/tree/dev/linodecli/plugins>`_)
are generated dynamically at build-time from the `Linode OpenAPI Specification <https://github.com/linode/linode-api-docs>`_,
which is also used to generate the `official Linode API documentation <https://www.linode.com/docs/api/>`_.

Each OpenAPI spec endpoint method is parsed into an :code:`OpenAPIOperation` object.
This object includes all necessary request and response arguments to create a command,
stored as :code:`OpenAPIRequestArg` and `OpenAPIResponseAttr` objects respectively.
At runtime, the Linode CLI changes each :code:`OpenAPIRequestArg` to an argparse argument and
each :code:`OpenAPIResponseAttr` to an outputtable column. It can also manage complex structures like
nested objects and lists, resulting in commands and outputs that may not
exactly match the OpenAPI specification.

OpenAPI Specification Extensions
--------------------------------

In order to better support the Linode CLI, the following `Specification Extensions <https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#specificationExtensions>`_ have been added to Linode's OpenAPI spec:

.. list-table::

   * - Attribute
     - Location
     - Purpose

   * - x-linode-cli-action
     - method
     - The action name for operations under this path. If not present, operationId is used.

   * - x-linode-cli-color
     - property
     - If present, defines key-value pairs of property value: color. Colors must be one of the `standard colors <https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors>`_ that accepted by Rich. Must include a default.

   * - x-linode-cli-command
     - path
     - The command name for operations under this path. If not present, "default" is used.

   * - x-linode-cli-display
     - property
     - If truthy, displays this as a column in output.  If a number, determines the ordering (left to right).

   * - x-linode-cli-format
     - property
     - Overrides the "format" given in this property for the CLI only.  Valid values are :code:`file` and `json`.

   * - x-linode-cli-skip
     - path
     - If present and truthy, this method will not be available in the CLI.

   * - x-linode-cli-allowed-defaults
     - requestBody
     - Tells the CLI what configured defaults apply to this request. Valid defaults are "region", "image", "authorized_users", "engine", and "type".

   * - x-linode-cli-nested-list
     - content-type
     - Tells the CLI to flatten a single object into multiple table rows based on the keys included in this value.  Values should be comma-delimited JSON paths, and must all be present on response objects. When used, a new key :code:`_split` is added to each flattened object whose value is the last segment of the JSON path used to generate the flattened object from the source.

   * - x-linode-cli-use-schema
     - content-type
     - Overrides the normal schema for the object and uses this instead. Especially useful when paired with :code:``x-linode-cli-nested-list``, allowing a schema to describe the flattened object instead of the original object.

   * - x-linode-cli-subtables
     - content-type
     - Indicates that certain response attributes should be printed in a separate "sub"-table. This allows certain endpoints with nested structures in the response to be displayed correctly.

Baking
------

The "baking" process is run with :code:`make bake`, `make install`, and `make build` targets,
wrapping the :code:`linode-cli bake` command.

Objects representing each command are serialized into the `data-3` file via the `pickle <https://docs.python.org/3/library/pickle.html>`_
package, and are included in release artifacts as a `data file <https://setuptools.pypa.io/en/latest/userguide/datafiles.html>`_.
This enables quick command loading at runtime and eliminates the need for runtime parsing logic.

Configuration
-------------

The Linode CLI can be configured using the :code:`linode-cli configure` command, which allows users to
configure the following:

- A Linode API token
  - This can optionally be done using OAuth, see `OAuth Authentication <#oauth-authentication>`_
- Default values for commonly used fields (e.g. region, image)
- Overrides for the target API URL (hostname, version, scheme, etc.)

This command serves as an interactive prompt and outputs a configuration file to :code:`~/.config/linode-cli`.
This file is in a simple INI format and can be easily modified manually by users.

Additionally, multiple users can be created for the CLI which can be designated when running commands using the :code:`--as-user` argument
or using the :code:`default-user` config variable.

When running a command, the config file is loaded into a :code:`CLIConfig` object stored under the `CLI.config` field.
This object allows various parts of the CLI to access the current user, the configured token, and any other CLI config values by name.

The logic for the interactive prompt and the logic for storing the CLI configuration can be found in the
:code:`configuration` package.

OAuth Authentication
--------------------

In addition to allowing users to configure a token manually, they can automatically generate a CLI token under their account using
an OAuth workflow. This workflow uses the `Linode OAuth API <https://www.linode.com/docs/api/#oauth>`_ to generate a temporary token,
which is then used to generate a long-term token stored in the CLI config file.

The OAuth client ID is hardcoded and references a client under an officially managed Linode account.

The rough steps of this OAuth workflow are as follows:

1. The CLI checks whether a browser can be opened. If not, manually prompt the user for a token and skip.
2. Open a local HTTP server on an arbitrary port that exposes :code:`oauth-landing-page.html`. This will also extract the token from the callback.
3. Open the user's browser to the OAuth URL with the hardcoded client ID and the callback URL pointing to the local webserver.
4. Once the user authorizes the OAuth application, they will be redirected to the local webserver where the temporary token will be extracted.
5. With the extracted token, a new token is generated with the default callback and a name similar to :code:`Linode CLI @ localhost`.

All the logic for OAuth token generation is stored in the :code:`configuration/auth.py` file.

Outputs
-------

The Linode CLI uses the `Rich Python package <https://rich.readthedocs.io/en/latest/>`_ to render tables, colorize text,
and handle other complex terminal output operations.

Output Overrides
----------------

For special cases where the desired output may not be possible using OpenAPI spec extensions alone, developers
can implement special override functions that are given the output JSON and print a custom output to stdout.

These overrides are specified using the :code:`@output_override` decorator and can be found in the `overrides.py` file.

Command Completions
-------------------

The Linode CLI allows users to dynamically generate shell completions for the Bash and Fish shells.
This works by rendering hardcoded templates for each baked/generated command.

See :code:`completion.py` for more details.

.. rubric:: Next Steps

To continue to the next step of this guide, continue to the :ref:`Setup page <development_setup>`.
