import os

import pytest

from tests.integration.database.fixtures import (  # noqa: F401
    mysql_cluster,
    postgresql_cluster,
    valkey_cluster,
)
from tests.integration.database.helpers import (
    database_command,
    database_json,
    get_db_type_id,
    get_engine_id,
    private_database_json,
    wait_for_database_status,
)
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_text,
    wait_for_condition,
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


def test_valkey_suspend_resume(valkey_cluster):
    database_id = str(valkey_cluster["id"])
    wait_for_database_status("valkey", database_id, "active")
    res = exec_test_command(
        BASE_CMDS["databases"]
        + ["valkey-suspend", database_id, "--text", "--delimiter=,"]
    )
    assert "Request failed: 400" not in res

    try:
        wait_for_database_status("valkey", database_id, "suspended")
    finally:
        res = exec_test_command(
            BASE_CMDS["databases"]
            + ["valkey-resume", database_id, "--text", "--delimiter=,"]
        )
        assert "Request failed: 400" not in res
        wait_for_database_status("valkey", database_id, "active")


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


def test_valkey_list():
    res = exec_test_command(
        BASE_CMDS["databases"] + ["valkey-list", "--text", "--delimiter=,"]
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


def test_valkey_discovery(valkey_cluster):
    engine = valkey_cluster["engine"]
    engines = database_json("engines")
    assert any(item["id"] == engine for item in engines)
    assert database_json("engine-view", engine)[0]["id"] == engine

    database_type = valkey_cluster["type"]
    types = database_json("types")
    assert any(
        item["id"] == database_type and item["_split"] == "valkey"
        for item in types
    )
    type_details = database_json("type-view", database_type)
    assert any(item["_split"] == "valkey" for item in type_details)


def test_valkey_in_databases_list(valkey_cluster):
    assert any(
        item["id"] == valkey_cluster["id"] for item in database_json("list")
    )


def test_valkey_credentials_and_ssl(valkey_cluster):
    database_id = valkey_cluster["id"]
    wait_for_database_status("valkey", database_id, "active")
    credentials = private_database_json("valkey-creds-view", database_id)
    assert isinstance(credentials.get("username"), str)
    assert credentials["username"]
    assert isinstance(credentials.get("password"), str)
    assert credentials["password"]

    certificate = private_database_json("valkey-ssl-cert", database_id)
    assert isinstance(certificate.get("ca_certificate"), str)
    assert certificate["ca_certificate"]

    exec_test_command(database_command("valkey-creds-reset", database_id))
    wait_for_condition(
        15,
        300,
        lambda: private_database_json("valkey-creds-view", database_id).get(
            "password"
        )
        not in (None, "", credentials["password"]),
    )


def test_valkey_patch(valkey_cluster):
    database_id = valkey_cluster["id"]
    wait_for_database_status("valkey", database_id, "active")
    exec_test_command(database_command("valkey-patch", database_id))
    assert database_json("valkey-view", database_id)[0]["id"] == database_id


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS") != "True",
    reason="Set RUN_LONG_TESTS=True to test Valkey snapshot restore",
)
def test_valkey_fork_from_snapshot(valkey_cluster):
    database_id = valkey_cluster["id"]
    wait_for_condition(
        30,
        1800,
        lambda: bool(
            database_json("valkey-view", database_id)[0][
                "available_restore_times"
            ]
        ),
    )
    restore_time = database_json("valkey-view", database_id)[0][
        "available_restore_times"
    ][-1]
    fork = database_json(
        "valkey-create",
        "--fork.source",
        database_id,
        "--fork.restore_time",
        restore_time,
        "--label",
        get_random_text(8) + "-valkey-fork",
        "--no-defaults",
    )[0]
    try:
        wait_for_database_status("valkey", fork["id"], "active")
        assert database_json("valkey-view", fork["id"])[0]["engine"] == "valkey"
    finally:
        delete_target_id(
            "databases",
            str(fork["id"]),
            delete_command="valkey-delete",
            use_retry=True,
            retries=5,
            delay=15,
        )
