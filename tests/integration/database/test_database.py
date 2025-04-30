import time

import pytest

from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
)
from tests.integration.linodes.helpers_linodes import DEFAULT_LABEL

BASE_CMD = ["linode-cli", "databases"]


def test_engines_list():
    res = (
        exec_test_command(BASE_CMD + ["engines", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["id", "engine", "version"]
    assert_headers_in_lines(headers, lines)


timestamp = str(time.time_ns())
mysql_database_label = DEFAULT_LABEL + "-mysql-" + timestamp
postgresql_database_label = DEFAULT_LABEL + "-postgresql-" + timestamp


@pytest.fixture(scope="package", autouse=True)
def test_mysql_cluster():
    database_id = (
        exec_test_command(
            BASE_CMD
            + [
                "mysql-create",
                "--type",
                "g6-nanode-1",
                "--region",
                "us-ord",
                "--label",
                mysql_database_label,
                "--engine",
                "mysql/8",
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format",
                "id",
                "--no-defaults",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield database_id

    delete_target_id(
        target="databases", delete_command="mysql-delete", id=database_id
    )


def test_mysql_suspend_resume(test_mysql_cluster):
    database_id = test_mysql_cluster
    res = exec_test_command(
        BASE_CMD + ["mysql-suspend", database_id, "--text", "--delimiter=,"]
    ).stdout.decode()
    assert "Request failed: 400" not in res

    res = exec_test_command(
        BASE_CMD + ["mysql-resume", database_id, "--text", "--delimiter=,"]
    ).stdout.decode()
    assert "Request failed: 400" not in res


@pytest.fixture(scope="package", autouse=True)
def test_postgresql_cluster():
    database_id = (
        exec_test_command(
            BASE_CMD
            + [
                "postgresql-create",
                "--type",
                "g6-nanode-1",
                "--region",
                "us-ord",
                "--label",
                postgresql_database_label,
                "--engine",
                "postgresql/16",
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format",
                "id",
                "--no-defaults",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield database_id

    delete_target_id(
        target="databases", delete_command="postgresql-delete", id=database_id
    )


def test_postgresql_suspend_resume(test_postgresql_cluster):
    database_id = test_postgresql_cluster
    res = exec_test_command(
        BASE_CMD
        + ["postgresql-suspend", database_id, "--text", "--delimiter=,"]
    ).stdout.decode()
    assert "Request failed: 400" not in res

    res = exec_test_command(
        BASE_CMD + ["postgresql-resume", database_id, "--text", "--delimiter=,"]
    ).stdout.decode()
    assert "Request failed: 400" not in res


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
