import json

import pytest

from tests.integration.database.helpers import (
    get_expected_keys_pg_engine_config,
)
from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_text,
)


@pytest.fixture(scope="session")
def postgresql_db_engine_config(linode_cloud_firewall):
    label = get_random_text(5) + "-postgresql-db"
    database = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "postgresql-create",
                "--engine",
                "postgresql/16",
                "--label",
                label,
                "--region",
                "us-east",
                "--type",
                "g6-standard-2",
                "--allow_list",
                "172.232.164.239",
                "--cluster_size",
                "3",
                "--ssl_connection",
                "true",
                "--engine_config.pg.autovacuum_analyze_scale_factor",
                "1",
                "--engine_config.pg.autovacuum_analyze_threshold",
                "2147483647",
                "--engine_config.pg.autovacuum_max_workers",
                "20",
                "--engine_config.pg.autovacuum_naptime",
                "86400",
                "--engine_config.pg.autovacuum_vacuum_cost_delay",
                "100",
                "--engine_config.pg.autovacuum_vacuum_cost_limit",
                "10000",
                "--engine_config.pg.autovacuum_vacuum_scale_factor",
                "1",
                "--engine_config.pg.autovacuum_vacuum_threshold",
                "2147483647",
                "--engine_config.pg.bgwriter_delay",
                "200",
                "--engine_config.pg.bgwriter_flush_after",
                "512",
                "--engine_config.pg.bgwriter_lru_maxpages",
                "100",
                "--engine_config.pg.bgwriter_lru_multiplier",
                "2.5",
                "--engine_config.pg.deadlock_timeout",
                "1000",
                "--engine_config.pg.default_toast_compression",
                "lz4",
                "--engine_config.pg.idle_in_transaction_session_timeout",
                "604800000",
                "--engine_config.pg.jit",
                "true",
                "--engine_config.pg.max_files_per_process",
                "1024",
                "--engine_config.pg.max_locks_per_transaction",
                "1024",
                "--engine_config.pg.max_logical_replication_workers",
                "64",
                "--engine_config.pg.max_parallel_workers",
                "96",
                "--engine_config.pg.max_parallel_workers_per_gather",
                "96",
                "--engine_config.pg.max_pred_locks_per_transaction",
                "5120",
                "--engine_config.pg.max_replication_slots",
                "64",
                "--engine_config.pg.max_slot_wal_keep_size",
                "1000000",
                "--engine_config.pg.max_stack_depth",
                "2097152",
                "--engine_config.pg.max_standby_archive_delay",
                "1",
                "--engine_config.pg.max_standby_streaming_delay",
                "10",
                "--engine_config.pg.max_wal_senders",
                "20",
                "--engine_config.pg.max_worker_processes",
                "96",
                "--engine_config.pg.password_encryption",
                "scram-sha-256",
                "--engine_config.pg.pg_partman_bgw.interval",
                "3600",
                "--engine_config.pg.pg_partman_bgw.role",
                "pg_partman_bgw",
                "--engine_config.pg.pg_stat_monitor.pgsm_enable_query_plan",
                "true",
                "--engine_config.pg.pg_stat_monitor.pgsm_max_buckets",
                "10",
                "--engine_config.pg.pg_stat_statements.track",
                "top",
                "--engine_config.pg.temp_file_limit",
                "5000000",
                "--engine_config.pg.timezone",
                "Europe/Helsinki",
                "--engine_config.pg.track_activity_query_size",
                "1024",
                "--engine_config.pg.track_commit_timestamp",
                "on",
                "--engine_config.pg.track_functions",
                "none",
                "--engine_config.pg.track_io_timing",
                "off",
                "--engine_config.pg.wal_sender_timeout",
                "60000",
                "--engine_config.pg.wal_writer_delay",
                "200",
                "--engine_config.pg_stat_monitor_enable",
                "true",
                "--engine_config.pglookout.max_failover_replication_time_lag",
                "10",
                "--json",
            ]
        )
    )[0]

    yield database["id"]

    delete_target_id("databases", str(database["id"]), "postgresql-delete")


# POSTGRESQL
def test_postgresql_engine_config_view():
    pg_configs = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "postgres-config-view",
                "--json",
            ]
        )
    )

    assert "pg" in pg_configs[0]
    pg_config = pg_configs[0]["pg"]

    assert "autovacuum_analyze_scale_factor" in pg_config
    assert pg_config["autovacuum_analyze_scale_factor"]["type"] == "number"
    assert pg_config["autovacuum_analyze_scale_factor"]["minimum"] == 0.0
    assert pg_config["autovacuum_analyze_scale_factor"]["maximum"] == 1.0

    assert "autovacuum_analyze_threshold" in pg_config
    assert pg_config["autovacuum_analyze_threshold"]["type"] == "integer"
    assert pg_config["autovacuum_analyze_threshold"]["minimum"] == 0
    assert pg_config["autovacuum_analyze_threshold"]["maximum"] == 2147483647

    assert "autovacuum_max_workers" in pg_config
    assert pg_config["autovacuum_max_workers"]["type"] == "integer"
    assert pg_config["autovacuum_max_workers"]["minimum"] == 1
    assert pg_config["autovacuum_max_workers"]["maximum"] == 20
    assert pg_config["autovacuum_max_workers"]["requires_restart"] is True

    assert "bgwriter_delay" in pg_config
    assert pg_config["bgwriter_delay"]["type"] == "integer"
    assert pg_config["bgwriter_delay"]["minimum"] == 10
    assert pg_config["bgwriter_delay"]["maximum"] == 10000

    assert "default_toast_compression" in pg_config
    assert pg_config["default_toast_compression"]["type"] == "string"
    assert "lz4" in pg_config["default_toast_compression"]["enum"]
    assert "pglz" in pg_config["default_toast_compression"]["enum"]

    assert "jit" in pg_config
    assert pg_config["jit"]["type"] == "boolean"

    assert "max_files_per_process" in pg_config
    assert pg_config["max_files_per_process"]["type"] == "integer"
    assert pg_config["max_files_per_process"]["requires_restart"] is True

    assert "max_logical_replication_workers" in pg_config
    assert pg_config["max_logical_replication_workers"]["type"] == "integer"
    assert (
        pg_config["max_logical_replication_workers"]["requires_restart"] is True
    )

    assert "password_encryption" in pg_config
    assert pg_config["password_encryption"]["type"] == "string"
    assert "md5" in pg_config["password_encryption"]["enum"]
    assert "scram-sha-256" in pg_config["password_encryption"]["enum"]

    assert "pg_partman_bgw.interval" in pg_config
    assert pg_config["pg_partman_bgw.interval"]["type"] == "integer"
    assert pg_config["pg_partman_bgw.interval"]["minimum"] == 3600

    assert "pg_partman_bgw.role" in pg_config
    assert pg_config["pg_partman_bgw.role"]["type"] == "string"
    assert pg_config["pg_partman_bgw.role"]["maxLength"] == 64

    assert "pg_stat_monitor.pgsm_enable_query_plan" in pg_config
    assert (
        pg_config["pg_stat_monitor.pgsm_enable_query_plan"]["type"] == "boolean"
    )
    assert (
        pg_config["pg_stat_monitor.pgsm_enable_query_plan"]["requires_restart"]
        is True
    )


def test_postgresql_list_with_engine_config(postgresql_db_engine_config):
    postgres_db_id = postgresql_db_engine_config

    postgres_dbs = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "postgresql-list",
                "--json",
            ]
        )
    )

    # Find the DB with the matching ID
    matching_db = next(
        (db for db in postgres_dbs if db["id"] == postgres_db_id), None
    )
    assert (
        matching_db is not None
    ), f"P DB with id {postgres_db_id} not found in mysql-list"

    engine_config = matching_db["engine_config"]
    assert "pg" in engine_config
    pg_config = engine_config["pg"]

    expected_pg_keys = get_expected_keys_pg_engine_config()

    for key in expected_pg_keys:
        assert key in pg_config

    assert "pg_stat_monitor_enable" in engine_config
    assert isinstance(engine_config["pg_stat_monitor_enable"], bool)

    pglookout = engine_config["pglookout"]
    assert isinstance(pglookout, dict)
    assert "max_failover_replication_time_lag" in pglookout
    assert isinstance(pglookout["max_failover_replication_time_lag"], int)


def test_postgresql_db_engine_config_view(postgresql_db_engine_config):
    postgres_db_id = postgresql_db_engine_config
    postgres_db = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "postgresql-view",
                str(postgres_db_id),
                "--json",
            ]
        )
    )

    db = postgres_db[0]

    engine_config = db["engine_config"]
    assert "pg" in engine_config
    pg_config = engine_config["pg"]

    expected_pg_keys = get_expected_keys_pg_engine_config()

    for key in expected_pg_keys:
        assert key in pg_config


def test_postgresql_db_engine_config_update(postgresql_db_engine_config):
    postgres_db_id = postgresql_db_engine_config
    updated_db = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "postgresql-update",
                str(postgres_db_id),
                "--engine_config.pg.autovacuum_analyze_scale_factor",
                "1",
                "--engine_config.pg.autovacuum_analyze_threshold",
                "2147483647",
                "--engine_config.pg.autovacuum_max_workers",
                "15",
                "--engine_config.pg.autovacuum_naptime",
                "86400",
                "--engine_config.pg.autovacuum_vacuum_cost_delay",
                "100",
                "--engine_config.pg.autovacuum_vacuum_cost_limit",
                "10000",
                "--engine_config.pg.autovacuum_vacuum_scale_factor",
                "1",
                "--engine_config.pg.autovacuum_vacuum_threshold",
                "2147483647",
                "--engine_config.pg.bgwriter_delay",
                "200",
                "--engine_config.pg.bgwriter_flush_after",
                "512",
                "--engine_config.pg.bgwriter_lru_maxpages",
                "100",
                "--engine_config.pg.bgwriter_lru_multiplier",
                "3.5",
                "--engine_config.pg.deadlock_timeout",
                "1000",
                "--engine_config.pg.default_toast_compression",
                "lz4",
                "--engine_config.pg.idle_in_transaction_session_timeout",
                "604800000",
                "--engine_config.pg.jit",
                "true",
                "--engine_config.pg.max_files_per_process",
                "1024",
                "--engine_config.pg.max_locks_per_transaction",
                "1024",
                "--engine_config.pg.max_logical_replication_workers",
                "64",
                "--engine_config.pg.max_parallel_workers",
                "96",
                "--engine_config.pg.max_parallel_workers_per_gather",
                "96",
                "--engine_config.pg.max_pred_locks_per_transaction",
                "5120",
                "--engine_config.pg.max_replication_slots",
                "64",
                "--engine_config.pg.max_slot_wal_keep_size",
                "1000000",
                "--engine_config.pg.max_stack_depth",
                "2097152",
                "--engine_config.pg.max_standby_archive_delay",
                "2",
                "--engine_config.pg.max_standby_streaming_delay",
                "10",
                "--engine_config.pg.max_wal_senders",
                "20",
                "--engine_config.pg.max_worker_processes",
                "96",
                "--engine_config.pg.password_encryption",
                "scram-sha-256",
                "--engine_config.pg.pg_partman_bgw.interval",
                "7200",
                "--engine_config.pg.pg_partman_bgw.role",
                "pg_partman_bgw",
                "--engine_config.pg.pg_stat_monitor.pgsm_enable_query_plan",
                "true",
                "--engine_config.pg.pg_stat_monitor.pgsm_max_buckets",
                "10",
                "--engine_config.pg.pg_stat_statements.track",
                "top",
                "--engine_config.pg.temp_file_limit",
                "5000000",
                "--engine_config.pg.timezone",
                "Europe/Helsinki",
                "--engine_config.pg.track_activity_query_size",
                "1024",
                "--engine_config.pg.track_commit_timestamp",
                "on",
                "--engine_config.pg.track_functions",
                "none",
                "--engine_config.pg.track_io_timing",
                "off",
                "--engine_config.pg.wal_sender_timeout",
                "60000",
                "--engine_config.pg.wal_writer_delay",
                "200",
                "--engine_config.pg_stat_monitor_enable",
                "true",
                "--engine_config.pglookout.max_failover_replication_time_lag",
                "10",
                "--json",
            ]
        )
    )

    db = updated_db[0]

    engine_config = db["engine_config"]
    assert "pg" in engine_config
    pg_config = engine_config["pg"]

    expected_pg_keys = get_expected_keys_pg_engine_config()

    for key in expected_pg_keys:
        assert key in pg_config

    assert pg_config["autovacuum_max_workers"] == 15
    assert pg_config["bgwriter_lru_multiplier"] == 3.5
    assert pg_config["pg_partman_bgw.interval"] == 7200


@pytest.fixture(scope="session")
def mysql_db_engine_config(linode_cloud_firewall):
    label = get_random_text(5) + "-mysql-db"
    database = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "mysql-create",
                "--engine",
                "mysql/8",
                "--label",
                label,
                "--region",
                "us-east",
                "--type",
                "g6-nanode-1",
                "--ssl_connection",
                "true",
                "--engine_config.binlog_retention_period",
                "86400",
                "--engine_config.mysql.connect_timeout",
                "10",
                "--engine_config.mysql.default_time_zone",
                "SYSTEM",
                "--engine_config.mysql.group_concat_max_len",
                "1024",
                "--engine_config.mysql.information_schema_stats_expiry",
                "900",
                "--engine_config.mysql.innodb_change_buffer_max_size",
                "25",
                "--engine_config.mysql.innodb_flush_neighbors",
                "1",
                "--engine_config.mysql.innodb_ft_min_token_size",
                "3",
                "--engine_config.mysql.innodb_ft_server_stopword_table",
                "mydb/stopword",
                "--engine_config.mysql.innodb_lock_wait_timeout",
                "50",
                "--engine_config.mysql.innodb_log_buffer_size",
                "16777216",
                "--engine_config.mysql.innodb_online_alter_log_max_size",
                "134217728",
                "--engine_config.mysql.innodb_read_io_threads",
                "4",
                "--engine_config.mysql.innodb_rollback_on_timeout",
                "true",
                "--engine_config.mysql.innodb_thread_concurrency",
                "8",
                "--engine_config.mysql.innodb_write_io_threads",
                "4",
                "--engine_config.mysql.interactive_timeout",
                "300",
                "--engine_config.mysql.internal_tmp_mem_storage_engine",
                "TempTable",
                "--engine_config.mysql.max_allowed_packet",
                "67108864",
                "--engine_config.mysql.max_heap_table_size",
                "16777216",
                "--engine_config.mysql.net_buffer_length",
                "8192",
                "--engine_config.mysql.net_read_timeout",
                "30",
                "--engine_config.mysql.net_write_timeout",
                "60",
                "--engine_config.mysql.sql_mode",
                "TRADITIONAL",
                "--engine_config.mysql.sql_require_primary_key",
                "true",
                "--engine_config.mysql.tmp_table_size",
                "16777216",
                "--engine_config.mysql.wait_timeout",
                "28800",
                "--json",
            ]
        )
    )[0]

    yield database["id"]

    delete_target_id("databases", str(database["id"]), "mysql-delete")


# MYSQL


def test_mysql_engine_config_view():
    mysql_config = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "mysql-config-view",
                "--json",
            ]
        )
    )

    assert "mysql" in mysql_config[0]
    assert "binlog_retention_period" in mysql_config[0]

    binlog_retention = mysql_config[0]["binlog_retention_period"]
    assert binlog_retention["type"] == "integer"
    assert binlog_retention["minimum"] == 600
    assert binlog_retention["maximum"] == 604800
    assert binlog_retention["requires_restart"] is False

    mysql_settings = mysql_config[0]["mysql"]
    assert "innodb_read_io_threads" in mysql_settings
    read_io = mysql_settings["innodb_read_io_threads"]
    assert read_io["requires_restart"] is True
    assert read_io["type"] == "integer"
    assert read_io["minimum"] == 1
    assert read_io["maximum"] == 64

    assert "internal_tmp_mem_storage_engine" in mysql_settings
    engine = mysql_settings["internal_tmp_mem_storage_engine"]
    assert engine["type"] == "string"
    assert "enum" in engine
    assert set(engine["enum"]) == {"TempTable", "MEMORY"}


def test_mysql_list_with_engine_config(mysql_db_engine_config):
    mysql_db_id = mysql_db_engine_config

    mysql_dbs = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "mysql-list",
                "--json",
            ]
        )
    )

    # Find the DB with the matching ID
    matching_db = next(
        (db for db in mysql_dbs if db["id"] == mysql_db_id), None
    )
    assert (
        matching_db is not None
    ), f"MySQL DB with id {mysql_db_id} not found in mysql-list"

    config = matching_db["engine_config"]
    mysql_config = config["mysql"]

    assert config["binlog_retention_period"] == 86400
    assert mysql_config["connect_timeout"] == 10
    assert mysql_config["default_time_zone"] == "SYSTEM"
    assert mysql_config["group_concat_max_len"] == 1024
    assert mysql_config["information_schema_stats_expiry"] == 900
    assert mysql_config["innodb_change_buffer_max_size"] == 25
    assert mysql_config["innodb_flush_neighbors"] == 1
    assert mysql_config["innodb_ft_min_token_size"] == 3
    assert mysql_config["innodb_ft_server_stopword_table"] == "mydb/stopword"
    assert mysql_config["innodb_lock_wait_timeout"] == 50
    assert mysql_config["innodb_log_buffer_size"] == 16777216
    assert mysql_config["innodb_online_alter_log_max_size"] == 134217728
    assert mysql_config["innodb_read_io_threads"] == 4
    assert mysql_config["innodb_rollback_on_timeout"] is True
    assert mysql_config["innodb_thread_concurrency"] == 8
    assert mysql_config["innodb_write_io_threads"] == 4
    assert mysql_config["interactive_timeout"] == 300
    assert mysql_config["internal_tmp_mem_storage_engine"] == "TempTable"
    assert mysql_config["max_allowed_packet"] == 67108864
    assert mysql_config["max_heap_table_size"] == 16777216
    assert mysql_config["net_buffer_length"] == 8192
    assert mysql_config["net_read_timeout"] == 30
    assert mysql_config["net_write_timeout"] == 60
    assert mysql_config["sql_mode"] == "TRADITIONAL"
    assert mysql_config["sql_require_primary_key"] is True
    assert mysql_config["tmp_table_size"] == 16777216
    assert mysql_config["wait_timeout"] == 28800


def test_mysql_db_view_with_engine_config(mysql_db_engine_config):
    mysql_db_id = mysql_db_engine_config

    mysql_db = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "mysql-view",
                str(mysql_db_id),
                "--json",
            ]
        )
    )

    db = mysql_db[0]

    assert db["engine"] == "mysql"
    assert db["status"] in ["active", "provisioning"]
    assert db["ssl_connection"] is True
    assert db["platform"] == "rdbms-default"
    assert db["label"].endswith("mysql-db")
    assert db["type"].startswith("g6-")
    engine_config = db.get("engine_config")
    assert engine_config["binlog_retention_period"] == 86400
    mysql_config = engine_config.get("mysql")
    assert mysql_config["innodb_lock_wait_timeout"] == 50
    assert mysql_config["sql_mode"] == "TRADITIONAL"
    assert mysql_config["sql_require_primary_key"] is True
    assert mysql_config["innodb_thread_concurrency"] == 8
    assert mysql_config["innodb_read_io_threads"] == 4
    assert mysql_config["group_concat_max_len"] == 1024
    assert "primary" in db["hosts"], "Expected 'primary' in hosts"


def test_mysql_db_engine_config_update(mysql_db_engine_config):
    mysql_db_id = mysql_db_engine_config

    mysql_db = json.loads(
        exec_test_command(
            BASE_CMDS["databases"]
            + [
                "mysql-update",
                str(mysql_db_id),
                "--engine_config.binlog_retention_period",
                "86400",
                "--engine_config.mysql.connect_timeout",
                "15",
                "--engine_config.mysql.default_time_zone",
                "SYSTEM",
                "--engine_config.mysql.group_concat_max_len",
                "1024",
                "--engine_config.mysql.information_schema_stats_expiry",
                "1000",
                "--engine_config.mysql.innodb_change_buffer_max_size",
                "25",
                "--engine_config.mysql.innodb_flush_neighbors",
                "1",
                "--engine_config.mysql.innodb_ft_min_token_size",
                "3",
                "--engine_config.mysql.innodb_ft_server_stopword_table",
                "mydb/stopword-updated",
                "--engine_config.mysql.innodb_lock_wait_timeout",
                "50",
                "--engine_config.mysql.innodb_log_buffer_size",
                "16777216",
                "--engine_config.mysql.innodb_online_alter_log_max_size",
                "134217728",
                "--engine_config.mysql.innodb_read_io_threads",
                "4",
                "--engine_config.mysql.innodb_rollback_on_timeout",
                "true",
                "--engine_config.mysql.innodb_thread_concurrency",
                "8",
                "--engine_config.mysql.innodb_write_io_threads",
                "4",
                "--engine_config.mysql.interactive_timeout",
                "300",
                "--engine_config.mysql.internal_tmp_mem_storage_engine",
                "TempTable",
                "--engine_config.mysql.max_allowed_packet",
                "67108864",
                "--engine_config.mysql.max_heap_table_size",
                "16777216",
                "--engine_config.mysql.net_buffer_length",
                "8192",
                "--engine_config.mysql.net_read_timeout",
                "30",
                "--engine_config.mysql.net_write_timeout",
                "60",
                "--engine_config.mysql.sql_mode",
                "STRICT_ALL_TABLES",
                "--engine_config.mysql.sql_require_primary_key",
                "true",
                "--engine_config.mysql.tmp_table_size",
                "16777216",
                "--engine_config.mysql.wait_timeout",
                "28800",
                "--json",
            ]
        )
    )[0]

    # Assertions for updated values
    assert mysql_db["engine_config"]["binlog_retention_period"] == 86400
    mysql = mysql_db["engine_config"]["mysql"]
    assert mysql["connect_timeout"] == 15
    assert mysql["default_time_zone"] == "SYSTEM"
    assert mysql["group_concat_max_len"] == 1024
    assert mysql["information_schema_stats_expiry"] == 1000
    assert mysql["innodb_change_buffer_max_size"] == 25
    assert mysql["innodb_flush_neighbors"] == 1
    assert mysql["innodb_ft_min_token_size"] == 3
    assert mysql["innodb_ft_server_stopword_table"] == "mydb/stopword-updated"
    assert mysql["innodb_lock_wait_timeout"] == 50
    assert mysql["innodb_log_buffer_size"] == 16777216
    assert mysql["innodb_online_alter_log_max_size"] == 134217728
    assert mysql["innodb_read_io_threads"] == 4
    assert mysql["innodb_rollback_on_timeout"] is True
    assert mysql["innodb_thread_concurrency"] == 8
    assert mysql["innodb_write_io_threads"] == 4
    assert mysql["interactive_timeout"] == 300
    assert mysql["internal_tmp_mem_storage_engine"] == "TempTable"
    assert mysql["max_allowed_packet"] == 67108864
    assert mysql["max_heap_table_size"] == 16777216
    assert mysql["net_buffer_length"] == 8192
    assert mysql["net_read_timeout"] == 30
    assert mysql["net_write_timeout"] == 60
    assert mysql["sql_mode"] == "STRICT_ALL_TABLES"
    assert mysql["sql_require_primary_key"] is True
    assert mysql["tmp_table_size"] == 16777216
    assert mysql["wait_timeout"] == 28800

    # Assertions for values that should not change
    assert mysql_db["label"].endswith("mysql-db")
    assert mysql_db["region"] == "us-east"
    assert mysql_db["cluster_size"] == 1
    assert mysql_db["engine"] == "mysql"
    assert mysql_db["version"].startswith("8")
    assert mysql_db["type"] == "g6-nanode-1"
    assert mysql_db["ssl_connection"] is True
    assert mysql_db["status"] in ["active", "provisioning"]
