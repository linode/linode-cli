.. _development_testing:

Testing
=======

This page gives an overview of how to run the various test suites for the Linode CLI.

Before running any tests, built and installed the Linode CLI with your changes using :code:`make install`.

Running Unit Tests
------------------

Unit tests can be run using the :code:`make testunit` Makefile target.

Running Integration Tests
-------------------------

Running the tests locally is simple. The only requirements are that you export Linode API token as :code:`LINODE_CLI_TOKEN`::

    export LINODE_CLI_TOKEN="your_token"

More information on Managing Linode API tokens can be found in our [API Token Docs](https://www.linode.com/docs/products/tools/api/guides/manage-api-tokens/).

In order to run the full integration test, run::

    make testint

To run specific test package, use environment variable :code:`INTEGRATION_TEST_PATH` with `testint` command::

    make INTEGRATION_TEST_PATH="cli" testint

Lastly, to run specific test case, use environment variables :code:`TEST_CASE` with `testint` command::

    make TEST_CASE=test_help_page_for_non_aliased_actions testint
