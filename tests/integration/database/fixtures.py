import json

import pytest

from tests.integration.database.helpers import wait_for_database_status
from tests.integration.helpers import (
    BASE_CMDS,
    DEFAULT_REGION,
    delete_target_id,
    exec_test_command,
    get_random_text,
)


@pytest.fixture(scope="module")
def postgresql_cluster():
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


@pytest.fixture(scope="module")
def mysql_cluster():
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
            "mysql/8.4",
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


@pytest.fixture(scope="session")
def valkey_cluster():
    commands = BASE_CMDS["databases"]
    engines = json.loads(exec_test_command(commands + ["engines", "--json"]))
    engine = next(
        (item["id"] for item in engines if item["id"].startswith("valkey/")),
        None,
    )
    assert engine is not None, "No Valkey engine is available"

    types = json.loads(exec_test_command(commands + ["types", "--json"]))
    plans = [
        (item["id"], item["engines"]["price"]["hourly"])
        for item in types
        if item.get("_split") == "valkey" and item["engines"]["quantity"] == 1
    ]
    assert plans, "No single-node Valkey database type is available"
    plan = min(plans, key=lambda entry: entry[1])[0]

    regions = json.loads(
        exec_test_command(["linode-cli", "regions", "list", "--json"])
    )
    supported_regions = [
        item["id"]
        for item in regions
        if "Managed Databases" in item["capabilities"]
        and item.get("status") == "ok"
    ]
    region = (
        DEFAULT_REGION
        if DEFAULT_REGION in supported_regions
        else next(iter(supported_regions), None)
    )
    assert region is not None, "No available Managed Databases region found"

    label = get_random_text(8) + "-valkey"
    created = json.loads(
        exec_test_command(
            commands
            + [
                "valkey-create",
                "--engine",
                engine,
                "--label",
                label,
                "--region",
                region,
                "--type",
                plan,
                "--engine_config.valkey_timeout",
                "301",
                "--engine_config.valkey_active_expire_effort",
                "2",
                "--engine_config.valkey_lfu_decay_time",
                "2",
                "--engine_config.valkey_lfu_log_factor",
                "11",
                "--engine_config.valkey_maxmemory_policy",
                "allkeys-lru",
                "--no-defaults",
                "--json",
            ]
        )
    )[0]
    database_id = created["id"]

    try:
        wait_for_database_status("valkey", database_id, "active")
        yield {
            "id": database_id,
            "engine": engine,
            "label": label,
            "region": region,
            "type": plan,
            "engine_config": {
                "valkey_timeout": 301,
                "valkey_active_expire_effort": 2,
                "valkey_lfu_decay_time": 2,
                "valkey_lfu_log_factor": 11,
                "valkey_maxmemory_policy": "allkeys-lru",
            },
        }
    finally:
        delete_target_id(
            target="databases",
            delete_command="valkey-delete",
            id=str(database_id),
            use_retry=True,
            retries=5,
            delay=15,
        )
