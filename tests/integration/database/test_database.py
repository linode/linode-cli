import pytest

from tests.integration.helpers import assert_headers_in_lines, exec_test_command

BASE_CMD = ["linode-cli", "databases"]
pytestmark = pytest.mark.skip(
    "This command is currently only available for customers who already have an active "
    "Managed Database."
)


def test_engines_list():
    res = (
        exec_test_command(BASE_CMD + ["engines", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["id", "engine", "version"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_engine_id():
    engine_id = (
        exec_test_command(
            BASE_CMD
            + [
                "engines",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )
    first_id = engine_id[0]
    yield first_id


def test_engines_view(get_engine_id):
    engine_id = get_engine_id
    res = (
        exec_test_command(
            BASE_CMD + ["engine-view", engine_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()

    headers = ["id", "engine", "version"]
    assert_headers_in_lines(headers, lines)


def test_databases_list():
    res = (
        exec_test_command(BASE_CMD + ["list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()

    headers = ["id", "label", "region"]
    assert_headers_in_lines(headers, lines)


def test_mysql_list():
    res = (
        exec_test_command(BASE_CMD + ["mysql-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()

    headers = ["id", "label", "region"]

    assert_headers_in_lines(headers, lines)


def test_postgresql_list():
    res = (
        exec_test_command(
            BASE_CMD + ["postgresql-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()

    headers = ["id", "label", "region"]

    assert_headers_in_lines(headers, lines)


def test_databases_types():
    res = (
        exec_test_command(BASE_CMD + ["types", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["id", "label", "_split"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_node_id():
    node_id = (
        exec_test_command(
            BASE_CMD
            + [
                "types",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )
    first_id = node_id[0]
    yield first_id


def test_databases_type_view(get_node_id):
    node_id = get_node_id
    res = (
        exec_test_command(
            BASE_CMD + ["type-view", node_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["id", "label", "_split"]
    assert_headers_in_lines(headers, lines)
