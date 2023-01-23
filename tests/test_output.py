import contextlib
import io

from linodecli import api_request, ModelAttr
from tests.test_populators import mock_cli, create_operation, list_operation


class TestOutputHandler:
    """
    Unit tests for linodecli.api_request
    """

    def test_markdown_output_columns(self, mock_cli):
        stdout_buf = io.StringIO()

        output_handler = mock_cli.output_handler

        with contextlib.redirect_stdout(stdout_buf):
            output_handler._markdown_output(
                ["very cool header", "wow"],
                [
                    ["foo", "bar"],
                    ["oof", "rab"]
                ],
                ["1", "2"]
            )

        assert stdout_buf.getvalue() == \
            "| very cool header | wow |\n" \
            "|---|---|\n" \
            "| foo | bar |\n" \
            "| oof | rab |\n"

    def test_markdown_output_models(self, mock_cli):
        stdout_buf = io.StringIO()

        output_handler = mock_cli.output_handler

        with contextlib.redirect_stdout(stdout_buf):
            output_handler._markdown_output(
                ["very cool header"],
                [
                    {
                        "cool": "foo"
                    },
                    {
                        "cool": "bar"
                    }
                ],
                [ModelAttr(
                    "cool",
                    True,
                    True,
                    "string"
                )]
            )

        assert stdout_buf.getvalue() == \
            "| very cool header |\n" \
            "|---|\n" \
            "| foo |\n" \
            "| bar |\n"
