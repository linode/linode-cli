import configparser

import pytest
from openapi3 import OpenAPI
from openapi3.paths import Path, Operation, Parameter, Response
from openapi3.schemas import Schema
from linodecli.baked.response import OpenAPIResponse, OpenAPIResponseAttr
from yaml import safe_load

from linodecli.cli import CLI
from linodecli.baked import OpenAPIOperation

MOCK_CONFIG = """
[DEFAULT]
default-user = testuser

[testuser]
region = us-southeast
image = linode/ubuntu21.10
token = notafaketoken
type = g6-nanode-1
mysql_engine = mysql/8.0.26
"""

LOADED_FILES = {}


def _get_parsed_yaml(filename):
    """
    Returns a python dict that is a parsed yaml file from the tests/fixtures
    directory.

    :param filename: The filename to load.  Must exist in tests/fixtures and
                     include extension.
    :type filename: str
    """
    if filename not in LOADED_FILES:
        with open("tests/fixtures/" + filename) as f:
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
    version="DEVELOPMENT",
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

    GET http://localhost/foo/bar
    {}

    X-Filter: {"filterable_result": "value"}
    """
    spec = _get_parsed_spec("example.yaml")

    print("parsed spec:, ", spec)

    for path in spec.paths.values():
        command = path.extensions.get("linode-cli-command", "default")

        operation = getattr(path, "get")

        method = "get"

        list_operation = make_test_operation(command, operation, method, path.parameters)

        return list_operation


@pytest.fixture
def create_operation():
    """
    Creates the following CLI operation:

    linode-cli foo bar --generic_arg [generic_arg] test_param

    POST http://localhost/foo/bar
    {
        "generic_arg": "[generic_arg]",
        "test_param": test_param
    }
    """

    return make_test_operation(
        command="foo",
        operation=['paths', '/foo/bar', 'post'],
        method="post",
        params=['paths', '/foo/bar', 'parameters', '0']
    )


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

