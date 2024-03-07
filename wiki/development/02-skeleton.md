# Linode CLI Skeleton

The following section outlines the purpose of each file in the CLI.

* `linode-cli`
  * `baked`
    * `__init__.py` - Contains imports for certain classes in this package
    * `colors.py` - Contains logic for colorizing strings in CLI outputs (deprecated)
    * `operation.py` - Contains the logic to parse an `OpenAPIOperation` from the OpenAPI spec and generate/execute a corresponding argparse parser
    * `request.py` - Contains the `OpenAPIRequest` and `OpenAPIRequestArg` classes
    * `response.py` - Contains `OpenAPIResponse` and `OpenAPIResponseAttr` classes
  * `configuration`
    * `__init__.py` - Contains the `CLIConfig` class and the logic for the interactive configuration prompt
    * `auth.py` - Contains all the logic for the token generation OAuth workflow
    * `helpers.py` - Contains various config-related helpers
  * `plugins`
    * `__init__.py` - Contains the shared wrapper that allows plugins to access CLI functionality
  * `__init__.py` -  Contains the main entrypoint for the CLI; routes top-level commands to their corresponding functions
  * `__main__.py` - Calls the project entrypoint in `__init__.py`
  * `api_request.py` - Contains logic for building API request bodies, making API requests, and handling API responses/errors
  * `arg_helpers.py` - Contains miscellaneous logic for registering common argparse arguments and loading the OpenAPI spec
  * `cli.py` - Contains the `CLI` class, which routes all the logic baking, loading, executing, and outputting generated CLI commands
  * `completion.py` - Contains all the logic for generating shell completion files (`linode-cli completion`)
  * `helpers.py` - Contains various miscellaneous helpers, especially relating to string manipulation, etc.
  * `oauth-landing-page.html` - The page to show users in their browser when the OAuth workflow is complete.
  * `output.py` - Contains all the logic for handling generated command outputs, including formatting tables, filtering JSON, etc.
  * `overrides.py` - Contains hardcoded output override functions for select CLI commands.
