import contextlib
import io

from linodecli import OutputMode


class TestOverrides:
    """
    Unit tests for linodecli.overrides
    """

    def test_domains_zone_file(self, mock_cli, list_operation):
        stdout_buf = io.StringIO()

        list_operation.command = "domains"
        list_operation.action = "zone-file"
        mock_cli.output_handler.mode = OutputMode.delimited

        with contextlib.redirect_stdout(stdout_buf):
            list_operation.process_response_json(
                {"zone_file": ["line 1", "line 2"]}, mock_cli.output_handler
            )

        assert stdout_buf.getvalue() == "line 1\nline 2\n"

        # Change the action to bypass the override
        list_operation.action = "zone-notfile"
        mock_cli.output_handler.mode = OutputMode.delimited
