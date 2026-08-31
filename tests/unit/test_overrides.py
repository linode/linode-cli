import contextlib
import io
from unittest.mock import patch

from linodecli import OutputMode
from linodecli.overrides import (
    OUTPUT_OVERRIDES,
    databases_mysql_config_view_output,
    databases_postgres_config_view_output,
    databases_valkey_config_view_output,
)


class MockConsole:
    """
    Mock rich console that captures the most recently printed table.
    """

    table = None

    def print(self, output):
        MockConsole.table = output


def _get_printed_parameter_names():
    return list(MockConsole.table.columns[0]._cells)


class TestOverrides:
    """
    Unit tests for linodecli.overrides
    """

    def test_domains_zone_file(
        self, mock_cli, list_operation_for_overrides_test
    ):
        response_json = {"zone_file": ["line 1", "line 2"]}
        override_signature = ("domains", "zone-file", OutputMode.delimited)

        list_operation_for_overrides_test.command = "domains"
        list_operation_for_overrides_test.action = "zone-file"
        mock_cli.output_handler.mode = OutputMode.delimited

        stdout_buf = io.StringIO()

        with contextlib.redirect_stdout(stdout_buf):
            list_operation_for_overrides_test.process_response_json(
                response_json, mock_cli.output_handler
            )

        assert stdout_buf.getvalue() == "line 1\nline 2\n"

        # Validate that the override will continue execution if it returns true
        def patch_func(*a):
            OUTPUT_OVERRIDES[override_signature](*a)
            return True

        with (
            patch(
                "linodecli.baked.operation.OUTPUT_OVERRIDES",
                {override_signature: patch_func},
            ),
            patch.object(mock_cli.output_handler, "print") as p,
        ):
            list_operation_for_overrides_test.process_response_json(
                response_json, mock_cli.output_handler
            )
            assert p.called

        # Change the action to bypass the override
        stdout_buf = io.StringIO()

        list_operation_for_overrides_test.action = "zone-notfile"
        mock_cli.output_handler.mode = OutputMode.delimited

        with contextlib.redirect_stdout(stdout_buf):
            list_operation_for_overrides_test.process_response_json(
                response_json, mock_cli.output_handler
            )

        assert stdout_buf.getvalue() != "line 1\nline 2\n"

    def test_types_region_prices_list(
        self, mock_cli, list_operation_for_overrides_test
    ):
        response_json = {
            "data": [
                {
                    "addons": {
                        "backups": {
                            "price": {"hourly": 0.008, "monthly": 5},
                            "region_prices": [
                                {
                                    "hourly": 0.0096,
                                    "id": "us-east",
                                    "monthly": 6,
                                }
                            ],
                        }
                    },
                    "class": "standard",
                    "disk": 81920,
                    "gpus": 0,
                    "id": "g6-standard-2",
                    "label": "Linode 4GB",
                    "memory": 4096,
                    "network_out": 1000,
                    "price": {"hourly": 0.03, "monthly": 20},
                    "region_prices": [
                        {"hourly": 0.036, "id": "us-east", "monthly": 24}
                    ],
                    "successor": None,
                    "transfer": 4000,
                    "vcpus": 2,
                }
            ],
            "page": 1,
            "pages": 1,
            "results": 1,
        }

        override_signature = ("linodes", "types", OutputMode.table)

        list_operation_for_overrides_test.command = "linodes"
        list_operation_for_overrides_test.action = "types"
        mock_cli.output_handler.mode = OutputMode.table

        stdout_buf = io.StringIO()

        with contextlib.redirect_stdout(stdout_buf):
            list_operation_for_overrides_test.process_response_json(
                response_json, mock_cli.output_handler
            )

        rows = stdout_buf.getvalue().split("\n")
        # assert that the overridden table has the new columns
        assert len(rows[1].split(rows[1][0])) == 15

    def test_database_config_output_recurses_nested_parameters(self):
        response_json = {
            "mysql": {
                "connect_timeout": {
                    "type": "integer",
                    "example": 10,
                    "minimum": 2,
                    "maximum": 3600,
                    "requires_restart": False,
                    "description": "Connect timeout.",
                }
            },
            "binlog_retention_period": {
                "type": "integer",
                "example": 600,
                "minimum": 600,
                "requires_restart": False,
                "description": "Binlog retention.",
            },
        }

        with patch("linodecli.overrides.Console", return_value=MockConsole()):
            assert databases_mysql_config_view_output(response_json) is False

        assert _get_printed_parameter_names() == [
            "mysql.connect_timeout",
            "binlog_retention_period",
        ]

    def test_database_config_output_preserves_postgres_top_level_parameters(
        self,
    ):
        response_json = {
            "pg": {
                "autovacuum_vacuum_scale_factor": {
                    "type": "number",
                    "example": 0.2,
                    "minimum": 0,
                    "maximum": 1,
                    "requires_restart": False,
                    "description": "Vacuum scale factor.",
                }
            },
            "work_mem": {
                "type": "integer",
                "example": 4,
                "minimum": 1,
                "maximum": 1024,
                "requires_restart": False,
                "description": "Working memory.",
            },
        }

        with patch("linodecli.overrides.Console", return_value=MockConsole()):
            assert databases_postgres_config_view_output(response_json) is False

        assert _get_printed_parameter_names() == [
            "pg.autovacuum_vacuum_scale_factor",
            "work_mem",
        ]

    def test_valkey_config_output_handles_flat_parameters(self):
        response_json = {
            "backup_minute": {
                "type": ["integer", "null"],
                "example": 30,
                "minimum": 0,
                "maximum": 59,
                "requires_restart": False,
                "description": "Backup minute.",
            },
            "valkey_persistence": {
                "type": "string",
                "enum": ["off", "rdb"],
                "requires_restart": True,
                "description": "Persistence mode.",
            },
        }

        with patch("linodecli.overrides.Console", return_value=MockConsole()):
            assert databases_valkey_config_view_output(response_json) is False

        assert _get_printed_parameter_names() == [
            "backup_minute",
            "valkey_persistence",
        ]
        assert (
            "databases",
            "valkey-config-view",
            OutputMode.table,
        ) in OUTPUT_OVERRIDES
