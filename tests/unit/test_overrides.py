import contextlib
import io
from unittest.mock import patch

from linodecli import OutputMode
from linodecli.overrides import OUTPUT_OVERRIDES


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

        with patch(
            "linodecli.baked.operation.OUTPUT_OVERRIDES",
            {override_signature: patch_func},
        ), patch.object(mock_cli.output_handler, "print") as p:
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
