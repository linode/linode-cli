import contextlib
import io

from terminaltables import SingleTable

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

    def test_json_output_delimited(self, mock_cli):
        output = io.StringIO()
        headers = ["foo", "bar"]
        data = [
            {
                "foo": "cool",
                "bar": "not cool"
            }
        ]

        mock_cli.output_handler._json_output(headers, data, output)

        assert '[{"foo": "cool", "bar": "not cool"}]' in output.getvalue()

    def test_json_output_list(self, mock_cli):
        output = io.StringIO()
        headers = ["foo", "bar"]
        data = [
            ["cool", "not cool"]
        ]

        mock_cli.output_handler._json_output(headers, data, output)

        assert '[{"foo": "cool", "bar": "not cool"}]' in output.getvalue()

    def test_select_json_elements(self, mock_cli):
        desired_keys = ["foo", "bar", "test"]

        result = mock_cli.output_handler._select_json_elements(
            desired_keys,
            {
                "foo": 12345,
                "bad": 5,
                "bar": 5,
                "good": {
                    "lol": "cool",
                    "test": "reallycoolvalue"
                },
                "test": 54321
            }
        )

        assert result == {
            "foo": 12345,
            "bar": 5,
            "good": {
                "test": "reallycoolvalue"
            },
            "test": 54321
        }

    def test_delimited_output_columns(self, mock_cli):
        output = io.StringIO()
        header = ["h1", "h2"]
        data = [
            ["foo", "bar"],
            ["oof", "rab"]
        ]
        columns = ["1", "2"]

        mock_cli.output_handler.delimiter = ","

        mock_cli.output_handler._delimited_output(
            header, data, columns, output
        )

        assert output.getvalue() == \
            "h1,h2\nfoo,bar\noof,rab\n"

    def test_delimited_output_models(self, mock_cli):
        output = io.StringIO()
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {
                "cool": "bar"
            }
        ]
        columns = [
            ModelAttr(
                "cool",
                True,
                True,
                "string"
            )
        ]

        mock_cli.output_handler.delimiter = ","

        mock_cli.output_handler._delimited_output(
            header, data, columns, output
        )

        assert output.getvalue() == \
            "h1\nfoo\nbar\n"

    def test_table_output_columns(self, mock_cli):
        output = io.StringIO()
        header = ["h1", "h2"]
        data = [
            ["foo", "bar"],
            ["oof", "rab"]
        ]
        columns = ["1", "2"]

        mock_cli.output_handler._table_output(
            header, data, columns, "cool table", output
        )

        mock_table = io.StringIO()
        tab = SingleTable([["h1", "h2"], ["foo", "bar"], ["oof", "rab"]])
        tab.title = "cool table"
        print(tab.table, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_table_output_models(self, mock_cli):
        output = io.StringIO()
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {
                "cool": "bar"
            }
        ]
        columns = [
            ModelAttr(
                "cool",
                True,
                True,
                "string"
            )
        ]

        mock_cli.output_handler._table_output(
            header, data, columns, "cool table", output
        )

        mock_table = io.StringIO()
        tab = SingleTable([["h1"], ["foo"], ["bar"]])
        tab.title = "cool table"
        print(tab.table, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()
