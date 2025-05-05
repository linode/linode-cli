import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_text,
)


@pytest.fixture(scope="package", autouse=True)
def test_postgresql_cluster():
    postgresql_database_label = get_random_text(5) + "_postgresql"

    database_id = exec_test_command(
        BASE_CMDS["databases"]
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

    yield database_id

    delete_target_id(
        target="databases", delete_command="postgresql-delete", id=database_id
    )


@pytest.fixture(scope="package", autouse=True)
def test_mysql_cluster():
    mysql_database_label = get_random_text(5) + "_mysql"

    database_id = exec_test_command(
        BASE_CMDS["databases"]
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

    yield database_id

    delete_target_id(
        target="databases", delete_command="mysql-delete", id=database_id
    )
