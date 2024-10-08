.. _development_project_skeleton:

Project Skeleton
================

This guide outlines the purpose of each file in the CLI.

linode-cli
----------

Contains all the logic for the `linode-cli` executable.

.. list-table::

   * - File
     - Purpose

   * - ``__init__.py``
     - Contains the main entrypoint for the CLI; routes top-level commands to their corresponding functions

   * - ``__main__.py``
     - Calls the project entrypoint in `__init__.py`

   * - ``api_request.py``
     - Contains logic for building API request bodies, making API requests, and handling API responses/errors

   * - ``arg_helpers.py``
     - Contains miscellaneous logic for registering common argparse arguments and loading the OpenAPI spec

   * - ``cli.py``
     - Contains the `CLI` class, which routes all the logic baking, loading, executing, and outputting generated CLI commands

   * - ``completion.py``
     - Contains all the logic for generating shell completion files (`linode-cli completion`)

   * - ``helpers.py``
     - Contains various miscellaneous helpers, especially relating to string manipulation, etc.

   * - ``oauth-landing-page.html``
     - The page to show users in their browser when the OAuth workflow is complete.

   * - ``output.py``
     - Contains all the logic for handling generated command outputs, including formatting tables, filtering JSON, etc.

   * - ``overrides.py``
     - Contains hardcoded output override functions for select CLI commands.

baked
^^^^^

This directory contains logic related to parsing, processing, serializing, and executing the Linode OpenAPI spec.

.. list-table::

   * - File
     - Purpose

   * - ``__init__.py``
     - Contains imports for certain classes in this package

   * - ``colors.py``
     - Contains logic for colorizing strings in CLI outputs (deprecated)

   * - ``operation.py``
     - Contains the logic to parse an `OpenAPIOperation` from the OpenAPI spec and generate/execute a corresponding argparse parser

   * - ``parsing.py``
     - Contains various logic related to parsing and translating text between markup languages.

   * - ``request.py``
     - Contains the `OpenAPIRequest` and `OpenAPIRequestArg` classes

   * - ``response.py``
     - Contains the `OpenAPIResponse` and `OpenAPIResponseAttr` classes

configuration
^^^^^^^^^^^^^

Contains all logic related to the configuring the Linode CLI.

.. list-table::

   * - File
     - Purpose

   * - ``__init__.py``
     - Contains imports for certain classes in this package

   * - ``auth.py``
     - Contains all the logic for the token generation OAuth workflow

   * - ``config.py``
     - Contains all the logic for loading, updating, and saving CLI configs

   * - ``helpers.py``
     - Contains various config-related helpers

documentation
^^^^^^^^^^^^^

Contains the logic and templates to generate documentation for the Linode CLI.

.. list-table::

   * - File
     - Purpose

   * - ``templates``
     - Contains the template files used to dynamically generate documentation pages

   * - ``__init__.py``
     - Contains imports for certain classes in this package

   * - ``generator.py``
     - Contains the logic to render and write documentation files

   * - ``template_data.py``
     - Contains all dataclasses used to render the documentation templates

plugins
^^^^^^^

Contains the default plugins and plugin SDK for this project.

.. list-table::

   * - File
     - Purpose

   * - ``__init__.py``
     - Contains imports for certain classes in this package

   * - ``plugins.py``
     - Contains the shared wrapper that allows plugins to access CLI functionality

docs
----

Contains the Sphinx configuration used to render the Linode CLI's documentation.

.. list-table::

   * - File
     - Purpose

   * - ``commands``
     - Contains non-generated documentation templates for the Linode CLI's commands.

   * - ``development``
     - Contains documentation templates for Linode CLI's development guide.

   * - ``conf.py``
     - Contains the Sphinx configuration for the Linode CLI's documentation

   * - ``index.rst``
     - The index/root document for the Linode CLI's documentation.

   * - ``Makefile``
     - Contains targets to render the documentation for this project


.. rubric:: Next Steps

To continue to the next step of this guide, continue to the :ref:`Testing page <development_testing>`.
