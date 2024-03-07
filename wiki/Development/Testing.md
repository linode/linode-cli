# Testing the CLI

## Running the Tests

Running the tests locally is simple. The only requirements are that you export Linode API token as `LINODE_CLI_TOKEN`::
```bash
export LINODE_CLI_TOKEN="your_token"
```

More information on Managing Linode API tokens can be found in our [API Token Docs](https://www.linode.com/docs/products/tools/api/guides/manage-api-tokens/).

In order to run the full integration test, run::
```bash
make testint
```

To run specific test package, use environment variable `INTEGRATION_TEST_PATH` with `testint` command::
```bash
make INTEGRATION_TEST_PATH="cli" testint
```

Lastly, to run specific test case, use environment variables `TEST_CASE` with `testint` command::
```bash
make TEST_CASE=test_help_page_for_non_aliased_actions testint
```
