from tests.integration.database.fixtures import (  # noqa: F401
    mysql_cluster,
    postgresql_cluster,
)
from tests.integration.database.helpers import get_db_type_id, get_engine_id
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
)


def test_engines_list():
    res = exec_test_command(
        BASE_CMDS["databases"] + ["engines", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["id", "engine", "version"]
    assert_headers_in_lines(headers, lines)


def test_mysql_suspend_resume(mysql_cluster):
    database_id = mysql_cluster
    res = exec_test_command(
        BASE_CMDS["databases"]
        + ["mysql-suspend", database_id, "--text", "--delimiter=,"]
    )
    assert "Request failed: 400" not in res

    res = exec_test_command(
        BASE_CMDS["databases"]
        + ["mysql-resume", database_id, "--text", "--delimiter=,"]
    )
    assert "Request failed: 400" not in res


def test_postgresql_suspend_resume(postgresql_cluster):
    database_id = postgresql_cluster
    res = exec_test_command(
        BASE_CMDS["databases"]
        + ["postgresql-suspend", database_id, "--text", "--delimiter=,"]
    )
    assert "Request failed: 400" not in res

    res = exec_test_command(
        BASE_CMDS["databases"]
        + ["postgresql-resume", database_id, "--text", "--delimiter=,"]
    )
    assert "Request failed: 400" not in res


def test_engines_view():
    engine_id = get_engine_id()
    res = exec_test_command(
        BASE_CMDS["databases"]
        + ["engine-view", engine_id, "--text", "--delimiter=,"]
    )

    lines = res.splitlines()

    headers = ["id", "engine", "version"]
    assert_headers_in_lines(headers, lines)


def test_databases_list():
    res = exec_test_command(
        BASE_CMDS["databases"] + ["list", "--text", "--delimiter=,"]
    )

    lines = res.splitlines()

    headers = ["id", "label", "region"]
    assert_headers_in_lines(headers, lines)


def test_mysql_list():
    res = exec_test_command(
        BASE_CMDS["databases"] + ["mysql-list", "--text", "--delimiter=,"]
    )

    lines = res.splitlines()

    headers = ["id", "label", "region"]

    assert_headers_in_lines(headers, lines)


def test_postgresql_list():
    res = exec_test_command(
        BASE_CMDS["databases"] + ["postgresql-list", "--text", "--delimiter=,"]
    )

    lines = res.splitlines()

    headers = ["id", "label", "region"]

    assert_headers_in_lines(headers, lines)


def test_databases_types():
    res = exec_test_command(
        BASE_CMDS["databases"] + ["types", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["id", "label", "_split"]
    assert_headers_in_lines(headers, lines)


def test_databases_type_view():
    db_type_id = get_db_type_id()
    res = exec_test_command(
        BASE_CMDS["databases"]
        + ["type-view", db_type_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["id", "label", "_split"]
    assert_headers_in_lines(headers, lines)
