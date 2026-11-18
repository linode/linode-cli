import json
import subprocess

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
    wait_for_condition,
)


def database_command(action, *args):
    return BASE_CMDS["databases"] + [action, *map(str, args)]


def database_json(action, *args):
    return json.loads(
        exec_test_command(database_command(action, *args, "--json"))
    )


def private_database_json(action, database_id):
    process = subprocess.run(
        database_command(action, database_id, "--json"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert (
        process.returncode == 0
    ), f"{action} failed (exit {process.returncode})"
    return json.loads(process.stdout)[0]


def wait_for_database_status(engine, database_id, status):
    wait_for_condition(
        15,
        900,
        lambda: database_json(f"{engine}-view", database_id)[0]["status"]
        == status,
    )


def get_db_type_id():
    db_type_ids = exec_test_command(
        BASE_CMDS["databases"]
        + [
            "types",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    return db_type_ids[0] if db_type_ids else None


def get_engine_id():
    engine_ids = exec_test_command(
        BASE_CMDS["databases"]
        + [
            "engines",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    return engine_ids[0] if engine_ids else None


def get_expected_keys_pg_engine_config():
    # Basic checks for pg config keys
    return [
        "autovacuum_analyze_scale_factor",
        "autovacuum_analyze_threshold",
        "autovacuum_max_workers",
        "autovacuum_naptime",
        "autovacuum_vacuum_cost_delay",
        "autovacuum_vacuum_cost_limit",
        "autovacuum_vacuum_scale_factor",
        "autovacuum_vacuum_threshold",
        "bgwriter_delay",
        "bgwriter_flush_after",
        "bgwriter_lru_maxpages",
        "bgwriter_lru_multiplier",
        "deadlock_timeout",
        "default_toast_compression",
        "idle_in_transaction_session_timeout",
        "jit",
        "max_files_per_process",
        "max_locks_per_transaction",
        "max_logical_replication_workers",
        "max_parallel_workers",
        "max_parallel_workers_per_gather",
        "max_pred_locks_per_transaction",
        "max_replication_slots",
        "max_slot_wal_keep_size",
        "max_stack_depth",
        "max_standby_archive_delay",
        "max_standby_streaming_delay",
        "max_wal_senders",
        "max_worker_processes",
        "password_encryption",
        "temp_file_limit",
        "timezone",
        "track_activity_query_size",
        "track_commit_timestamp",
        "track_functions",
        "track_io_timing",
        "wal_sender_timeout",
        "wal_writer_delay",
    ]
