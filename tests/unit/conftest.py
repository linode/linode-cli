import configparser
import contextlib
import os
from typing import ContextManager, List, TextIO

import pytest
from openapi3 import OpenAPI
from openapi3.paths import Operation, Parameter
from yaml import safe_load

from linodecli.baked import OpenAPIOperation
from linodecli.cli import CLI

MOCK_CONFIG = """
[DEFAULT]
default-user = testuser

[testuser]
region = us-southeast
image = linode/ubuntu21.10
token = notafaketoken
type = g6-nanode-1
"""

LOADED_FILES = {}


FIXTURES_PATH = "tests/fixtures"


@contextlib.contextmanager
def open_fixture(filename: str) -> ContextManager[TextIO]:
    """
    Gets the reader for a given fixture.

    :returns: A context manager yielding the fixture's reader.
    """

    f = open(os.path.join(FIXTURES_PATH, filename), "r")

    try:
        yield f
    finally:
        f.close()


def _get_parsed_yaml(filename):
    """
    Returns a python dict that is a parsed yaml file from the tests/fixtures
    directory.

    :param filename: The filename to load.  Must exist in tests/fixtures and
                     include extension.
    :type filename: str
    """
    if filename not in LOADED_FILES:
        with open_fixture(filename) as f:
            raw = f.read()

        parsed = safe_load(raw)

        LOADED_FILES[filename] = parsed

    return LOADED_FILES[filename]


def _get_parsed_spec(filename):
    """
    Returns an OpenAPI object loaded from a file in the tests/fixtures directory

    :param filename: The filename to load.  Must exist in tests/fixtures and
                     include extension.
    :type filename: str
    """
    if "spec:" + filename not in LOADED_FILES:
        parsed = _get_parsed_yaml(filename)

        spec = OpenAPI(parsed)

        LOADED_FILES["spec:" + filename] = spec

    return LOADED_FILES["spec:" + filename]


@pytest.fixture
def mock_cli(
    version="0.0.0",
    url="http://localhost",
    defaults=True,
):
    result = CLI(version, url, skip_config=True)
    result.defaults = defaults
    result.suppress_warnings = True

    # Let's override the config with a custom one
    conf = configparser.ConfigParser()
    conf.read_string(MOCK_CONFIG)

    result.config.config = conf
    result.config._configured = True

    # very evil pattern :)
    # We need this to suppress warnings for operations that don't
    # have access to the cli.suppress_warnings attribute.
    # e.g. operation defaults
    # sys.argv.append("--suppress-warnings")

    return result


def make_test_operation(
    command,
    operation: Operation,
    method,
    params: Parameter,
):
    return OpenAPIOperation(
        command=command,
        operation=operation,
        method=method,
        params=params,
    )


@pytest.fixture
def list_operation():
    """
    Creates the following CLI operation:

    linode-cli foo bar --filterable_result [value]

    GET http://localhost/v4/foo/bar
    {}

    X-Filter: {"filterable_result": "value"}
    """
    spec = _get_parsed_spec("api_request_test_foobar_get.yaml")

    dict_values = list(spec.paths.values())

    # Get parameters for OpenAPIOperation() from yaml fixture
    path = dict_values[0]
    command = path.extensions.get("linode-cli-command", "default")
    operation = getattr(path, "get")
    method = "get"

    list_operation = make_test_operation(
        command, operation, method, path.parameters
    )

    return list_operation


@pytest.fixture
def create_operation():
    """
    Creates the following CLI operation:

    linode-cli foo bar --generic_arg [generic_arg] test_param

    POST http://localhost/v4/foo/bar
    {
        "generic_arg": "[generic_arg]",
        "test_param": test_param
    }
    """

    spec = _get_parsed_spec("api_request_test_foobar_post.yaml")

    dict_values = list(spec.paths.values())

    # Get parameters for OpenAPIOperation() from yaml fixture
    path = dict_values[0]
    command = path.extensions.get("linode-cli-command", "default")
    operation = getattr(path, "post")
    method = "post"

    create_operation = make_test_operation(
        command, operation, method, path.parameters
    )

    return create_operation


@pytest.fixture
def update_operation():
    """
    Creates the following CLI operation:

    linode-cli foo bar-update --generic_arg [generic_arg] test_param

    PUT http://localhost/v4/foo/bar/{fooId}
    {
        "generic_arg": "[generic_arg]",
        "test_param": test_param
    }
    """

    spec = _get_parsed_spec("api_request_test_foobar_put.yaml")

    dict_values = list(spec.paths.values())

    # Get parameters for OpenAPIOperation() from yaml fixture
    path = dict_values[0]
    command = path.extensions.get("linode-cli-command", "default")
    operation = getattr(path, "put")
    method = "put"

    create_operation = make_test_operation(
        command, operation, method, path.parameters
    )

    return create_operation


@pytest.fixture
def list_operation_for_output_tests():
    """
    Creates the following CLI operation:

    GET http://localhost/v4/foo/bar
    {}

    X-Filter: {"cool": "value"}
    """

    spec = _get_parsed_spec("output_test_get.yaml")

    dict_values = list(spec.paths.values())

    # Get parameters for OpenAPIOperation() from yaml fixture
    path = dict_values[0]
    command = path.extensions.get("linode-cli-command", "default")
    operation = getattr(path, "get")
    method = "get"

    cool_operation = make_test_operation(
        command, operation, method, path.parameters
    )

    return cool_operation


@pytest.fixture
def list_operation_for_overrides_test():
    """
    Creates the following CLI operation:

    GET http://localhost/v4/foo/bar
    {}

    X-Filter: {"cool": "value"}
    """

    spec = _get_parsed_spec("overrides_test_get.yaml")

    dict_values = list(spec.paths.values())

    # Get parameters for OpenAPIOperation() from yaml fixture
    path = dict_values[0]

    command = path.extensions.get("linode-cli-command", "default")
    operation = getattr(path, "get")
    method = "get"

    cool_operation = make_test_operation(
        command, operation, method, path.parameters
    )

    return cool_operation


@pytest.fixture
def list_operation_for_response_test():
    """
    Creates the following CLI operation:

    GET http://localhost/v4/foo/bar
    {}

    X-Filter: {"cool": "value"}
    """

    spec = _get_parsed_spec("response_test_get.yaml")

    dict_values = list(spec.paths.values())

    # Get parameters for OpenAPIOperation() from yaml fixture
    path = dict_values[0]

    command = path.extensions.get("linode-cli-command", "default")
    operation = getattr(path, "get")
    method = "get"

    cool_operation = make_test_operation(
        command, operation, method, path.parameters
    )

    return cool_operation


@pytest.fixture
def get_operation_for_subtable_test():
    """
    Creates the following CLI operation:

    GET http://localhost/v4/foo/bar

    Returns {
        "table": [
            {
                "foo": "",
                "bar": 0
            }
        ],
        "foo": {
            "single_nested": {
                "foo": "",
                "bar": ""
            },
            "table": [
                {
                    "foobar": ["127.0.0.1"]
                }
            ]
        },
        "foobar": ""
    }
    """

    spec = _get_parsed_spec("subtable_test_get.yaml")

    dict_values = list(spec.paths.values())

    # Get parameters for OpenAPIOperation() from yaml fixture
    path = dict_values[0]

    command = path.extensions.get("linode-cli-command", "default")
    operation = getattr(path, "get")
    method = "get"

    return make_test_operation(command, operation, method, path.parameters)


@pytest.fixture
def get_openapi_for_api_components_tests() -> OpenAPI:
    """
    Creates a set of OpenAPI operations with various apiVersion and
    `server` configurations.
    """

    return _get_parsed_spec("api_url_components_test.yaml")


@pytest.fixture
def get_openapi_for_docs_url_tests() -> OpenAPI:
    """
    Creates a set of OpenAPI operations with a GET endpoint using the
    legacy-style docs URL and a POST endpoint using the new-style docs URL.
    """

    return _get_parsed_spec("docs_url_test.yaml")


@pytest.fixture
def mocked_config():
    """
    mock config representing cli.config
    """

    class Config:
        config = configparser.ConfigParser()

        def write_config(self):  # pylint: disable=missing-function-docstring
            pass

    return Config()


def assert_contains_ordered_substrings(target: str, entries: List[str]):
    """
    Asserts whether the given string contains the given entries in order,
    ignoring any irrelevant characters in-between.

    :param target: The string to search.
    :param entries: The ordered list of entries to search for.
    """

    start_index = 0

    for entry in entries:
        find_index = target[start_index:].find(entry)
        assert find_index >= 0

        # Search for the next entry after the end of this entry
        start_index = find_index + len(entry)
