from tests.integration.helpers import exec_test_command

BASE_CMD = ["linode-cli", "databases"]


def test_engines_list():
    res = (
        exec_test_command(BASE_CMD + ["engines", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    engine_id = lines[1].split(",")[0]

    headers = ["id", "engine", "version"]
    for header in headers:
        assert header in lines[0]
    return engine_id


def test_engines_view():
    engine_id = test_engines_list()
    res = (
        exec_test_command(
            BASE_CMD + ["engine-view", engine_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()

    headers = ["id", "engine", "version"]
    for header in headers:
        assert header in lines[0]


def test_databases_list():
    res = (
        exec_test_command(BASE_CMD + ["list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()

    headers = ["id", "label", "region"]
    for header in headers:
        assert header in lines[0]


def test_mysql_list():
    res = (
        exec_test_command(BASE_CMD + ["mysql-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()

    headers = ["id", "label", "region"]

    for header in headers:
        assert header in lines[0]


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

    for header in headers:
        assert header in lines[0]


def test_databases_types():
    res = (
        exec_test_command(BASE_CMD + ["types", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    node_id = lines[1].split(",")[0]

    headers = ["id", "label", "_split"]
    for header in headers:
        assert header in lines[0]
    return node_id


def test_databases_type_view():
    node_id = test_databases_types()
    res = (
        exec_test_command(
            BASE_CMD + ["type-view", node_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["id", "label", "_split"]
    for header in headers:
        assert header in lines[0]
