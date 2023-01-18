import configparser

from linodecli import ResponseModel, CLIOperation, URLParam, ModelAttr, CLIArg
from linodecli.cli import CLI

MOCK_CONFIG = """
[DEFAULT]
default-user = testuser

[testuser]
region = us-southeast
image = linode/ubuntu21.10
authorized_users = lgarber-dev
type = g6-nanode-1
"""

def make_test_cli(
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

    return result

def make_test_operation(
        command,
        action,
        method,
        url,
        summary,
        args,
        response_model,
        use_params,
        use_servers=None,
        docs_url="https://localhost/docs",
        allowed_defaults=None,
        action_aliases=None
):
    if args is None:
        args = [
            CLIArg(
                "generic_arg",
                "string",
                "Does something maybe.",
                "generic_arg",
                None
            )
        ]

    if use_params is None:
        use_params = [URLParam("test_param", "integer")]

    if use_servers is None:
        use_servers = ["http://localhost"]

    if allowed_defaults is None:
        allowed_defaults = []

    if action_aliases is None:
        action_aliases = []

    return CLIOperation(
        command,
        action,
        method,
        url,
        summary,
        args,
        response_model,
        use_params,
        use_servers,
        docs_url=docs_url,
        allowed_defaults=allowed_defaults,
        action_aliases=action_aliases
    )


def make_test_list_operation():
    """
    Creates the following CLI operation:

    linode-cli foo bar --filterable_result [value]

    GET http://localhost/foo/bar
    {}

    X-Filter: {"filterable_result": "value"}
    """

    return make_test_operation(
        "foo",
        "bar",
        "get",
        "foo/bar",
        "get info",
        [],
        ResponseModel([
            ModelAttr(
                "filterable_result",
                True,
                True,
                "string"
            )
        ]),
        []
    )


def make_test_create_operation():
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
        "foo",
        "bar",
        "post",
        "foo/bar",
        "create something",
        [
            CLIArg(
                "generic_arg",
                "string",
                "Does something maybe.",
                "generic_arg",
                None
            ),
            CLIArg(
                "region",
                "string",
                "a region",
                "region",
                None
            )
        ],
        ResponseModel([
            ModelAttr(
                "result",
                False,
                True,
                "string"
            )
        ]),
        [URLParam("test_param", "integer")]
    )
