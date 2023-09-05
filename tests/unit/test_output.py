import io
import json

from rich import box
from rich import print as rprint
from rich.table import Table

from linodecli import OutputMode


class TestOutputHandler:
    """
    Unit tests for linodecli.output
    """

    def test_json_output_delimited(self, mock_cli):
        output = io.StringIO()
        headers = ["foo", "bar"]
        data = [{"foo": "cool", "bar": "not cool"}]

        mock_cli.output_handler._json_output(headers, data, output)

        assert '[{"foo": "cool", "bar": "not cool"}]' in output.getvalue()

    def test_json_output_list(self, mock_cli):
        output = io.StringIO()
        headers = ["foo", "bar"]
        data = [["cool", "not cool"]]

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
                "good": {"lol": "cool", "test": "reallycoolvalue"},
                "test": 54321,
            },
        )

        assert result == {
            "foo": 12345,
            "bar": 5,
            "good": {"test": "reallycoolvalue"},
            "test": 54321,
        }

    def test_delimited_output_columns(self, mock_cli):
        output = io.StringIO()
        header = ["h1", "h2"]
        data = [["foo", "bar"], ["oof", "rab"]]
        columns = ["1", "2"]

        mock_cli.output_handler.delimiter = ","

        mock_cli.output_handler._delimited_output(header, data, columns, output)

        assert output.getvalue() == "h1,h2\nfoo,bar\noof,rab\n"

    def test_delimited_output_models(
        self, mock_cli, list_operation_for_output_tests
    ):
        output = io.StringIO()
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {"cool": "bar"},
        ]

        attr = list_operation_for_output_tests.response_model.attrs[0]
        columns = [attr]

        mock_cli.output_handler.delimiter = ","

        mock_cli.output_handler._delimited_output(header, data, columns, output)

        assert output.getvalue() == "h1\nfoo\nbar\n"

    def test_table_output_columns(self, mock_cli):
        output = io.StringIO()
        header = ["h1", "h2"]
        data = [["foo", "bar"], ["oof", "rab"]]
        columns = ["1", "2"]

        mock_cli.output_handler._table_output(
            header, data, columns, "cool table", output
        )

        mock_table = io.StringIO()
        tab = Table(
            "h1", "h2", header_style="", box=box.SQUARE, title_justify="left"
        )
        for row in [["foo", "bar"], ["oof", "rab"]]:
            tab.add_row(*row)
        tab.title = "cool table"
        rprint(tab, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_table_output_models(
        self, mock_cli, list_operation_for_output_tests
    ):
        output = io.StringIO()

        title = "cool table"
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {"cool": "bar"},
        ]

        attr = list_operation_for_output_tests.response_model.attrs[0]
        columns = [attr]

        mock_cli.output_handler._table_output(
            header, data, columns, title, output
        )

        mock_table = io.StringIO()
        tab = Table(
            "h1",
            header_style="",
            box=box.SQUARE,
            title_justify="left",
            title=title,
            min_width=len(title),
        )
        for row in [["foo"], ["bar"]]:
            tab.add_row(*row)
        rprint(tab, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_table_output_models_no_headers(
        self, mock_cli, list_operation_for_output_tests
    ):
        mock_cli.output_handler.headers = False

        output = io.StringIO()

        title = "cool table"
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {"cool": "bar"},
        ]
        columns = [list_operation_for_output_tests.response_model.attrs[0]]

        mock_cli.output_handler._table_output(
            header, data, columns, "cool table", output
        )

        mock_table = io.StringIO()
        tab = Table(
            header_style="",
            show_header=False,
            box=box.SQUARE,
            title_justify="left",
        )
        for row in [["foo"], ["bar"]]:
            tab.add_row(*row)
        rprint(tab, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_ascii_table_output(
        self, mock_cli, list_operation_for_output_tests
    ):
        output = io.StringIO()

        title = "cool table"
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {"cool": "bar"},
        ]
        columns = [list_operation_for_output_tests.response_model.attrs[0]]

        output_handler = mock_cli.output_handler
        output_handler._table_output(
            header, data, columns, title, output, box.ASCII
        )

        print(output.getvalue())

        assert (
            output.getvalue() == "cool table\n"
            "+--------+\n"
            "| h1     |\n"
            "|--------|\n"
            "| foo    |\n"
            "| bar    |\n"
            "+--------+\n"
        )

    def test_get_columns_from_model(
        self, mock_cli, list_operation_for_output_tests
    ):
        output_handler = mock_cli.output_handler

        result = output_handler._get_columns(
            list_operation_for_output_tests.response_model.attrs
        )

        assert len(result) == 3
        assert result[0].name == "cool"
        assert result[1].name == "bar"
        assert result[2].name == "test"

    def test_get_columns_from_model_all(
        self, mock_cli, list_operation_for_output_tests
    ):
        output_handler = mock_cli.output_handler

        output_handler.columns = "*"

        result = output_handler._get_columns(
            list_operation_for_output_tests.response_model.attrs
        )

        assert len(result) == 3
        assert result[0].name == "cool"
        assert result[1].name == "bar"
        assert result[2].name == "test"

    def test_get_columns_from_model_select(
        self, mock_cli, list_operation_for_output_tests
    ):
        output_handler = mock_cli.output_handler

        output_handler.columns = "cool,bar"

        result = output_handler._get_columns(
            list_operation_for_output_tests.response_model.attrs
        )

        assert len(result) == 2
        assert result[0].name == "cool"
        assert result[1].name == "bar"

        # Let's test a single print case

    def test_print_raw(self, mock_cli):
        output = io.StringIO()

        mock_cli.output_handler.mode = OutputMode.json

        mock_cli.output_handler.print(
            [{"cool": "blah", "bar": "blah2", "test": "blah3"}],
            ["cool", "bar", "test"],
            to=output,
        )

        assert (
            '[{"cool": "blah", "bar": "blah2", "test": "blah3"}]'
            in output.getvalue()
        )

    # Let's test a single print case
    def test_print_response(self, mock_cli, list_operation_for_output_tests):
        output = io.StringIO()

        response_model = list_operation_for_output_tests.response_model

        mock_cli.output_handler.mode = OutputMode.json

        mock_cli.output_handler.print_response(
            response_model,
            [{"cool": "blah", "bar": "blah2", "test": "blah3"}],
            to=output,
        )

        assert (
            '[{"cool": "blah", "bar": "blah2", "test": "blah3"}]'
            in output.getvalue()
        )

    def test_truncated_table(self, mock_cli, list_operation_for_output_tests):
        mock_cli.output_handler.column_width = 2

        output = io.StringIO()

        title = "cool table"
        test_str = "x" * 80
        test_str_truncated = "x…"

        header = ["h1"]
        data = [
            {
                "cool": test_str,
            },
        ]
        columns = [list_operation_for_output_tests.response_model.attrs[0]]

        mock_cli.output_handler._table_output(
            header, data, columns, title, output
        )

        data[0]["cool"] = test_str_truncated

        mock_table = io.StringIO()
        tab = Table(
            "h1",
            header_style="",
            box=box.SQUARE,
            title_justify="left",
            title=title,
        )
        tab.add_row(test_str_truncated)
        rprint(tab, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_nontruncated_table(
        self, mock_cli, list_operation_for_output_tests
    ):
        mock_cli.output_handler.column_width = 2
        mock_cli.output_handler.disable_truncation = True

        output = io.StringIO()

        test_str = "x" * 80
        test_str_truncated = "x…"

        header = ["h1"]
        data = [
            {
                "cool": test_str,
            },
        ]
        columns = [list_operation_for_output_tests.response_model.attrs[0]]

        mock_cli.output_handler._table_output(
            header, data, columns, "cool table", output
        )

        data[0]["cool"] = test_str_truncated

        mock_table = io.StringIO()
        tab = Table("h1", header_style="", box=box.SQUARE, title_justify="left")
        tab.add_row(test_str_truncated)
        tab.title = "cool table"
        rprint(tab, file=mock_table)

        assert output.getvalue() != mock_table.getvalue()

    def test_print_subtable(self, mock_cli, get_operation_for_subtable_test):
        output = io.StringIO()

        mock_cli.output_handler.mode = OutputMode.table

        mock_data = {
            "table": [{"foo": "cool", "bar": 12345}],
            "foo": {
                "single_nested": {"foo": "cool", "bar": "cool2"},
                "table": [{"foobar": ["127.0.0.1", "127.0.0.2"]}],
            },
            "foobar": "wow",
        }

        mock_cli.output_handler.print_response(
            get_operation_for_subtable_test.response_model,
            data=[mock_data],
            to=output,
        )

        output = output.getvalue().splitlines()

        lines = [
            "┌────────┐",
            "│ foobar │",
            "├────────┤",
            "│ wow    │",
            "└────────┘",
            "table",
            "┌──────┬───────┐",
            "│ foo  │ bar   │",
            "├──────┼───────┤",
            "│ cool │ 12345 │",
            "└──────┴───────┘",
            "foo.table",
            "┌──────────────────────┐",
            "│ foobar               │",
            "├──────────────────────┤",
            "│ 127.0.0.1, 127.0.0.2 │",
            "└──────────────────────┘",
            "foo.single_nested",
            "┌───────┬───────┐",
            "│ foo   │ bar   │",
            "├───────┼───────┤",
            "│ cool  │ cool2 │",
            "└───────┴───────┘",
        ]

        for i, line in enumerate(lines):
            assert line in output[i]

    def test_print_subtable_json(
        self, mock_cli, get_operation_for_subtable_test
    ):
        output = io.StringIO()

        mock_cli.output_handler.mode = OutputMode.json

        mock_data = {
            "table": [{"foo": "cool", "bar": 12345}],
            "foo": {
                "single_nested": {"foo": "cool", "bar": "cool2"},
                "table": [{"foobar": ["127.0.0.1", "127.0.0.2"]}],
            },
            "foobar": "wow",
        }

        mock_cli.output_handler.print_response(
            get_operation_for_subtable_test.response_model,
            data=[mock_data],
            to=output,
        )

        output = json.loads(output.getvalue())
        assert output == [mock_data]

    def test_print_subtable_delimited(
        self, mock_cli, get_operation_for_subtable_test
    ):
        output = io.StringIO()

        mock_cli.output_handler.mode = OutputMode.delimited

        mock_data = {
            "table": [{"foo": "cool", "bar": 12345}],
            "foo": {
                "single_nested": {"foo": "cool", "bar": "cool2"},
                "table": [{"foobar": ["127.0.0.1", "127.0.0.2"]}],
            },
            "foobar": "wow",
        }

        mock_cli.output_handler.print_response(
            get_operation_for_subtable_test.response_model,
            data=[mock_data],
            to=output,
        )

        output = output.getvalue().splitlines()

        lines = [
            "foobar",
            "wow",
            "",
            "table",
            "foo\tbar",
            "cool\t12345",
            "",
            "foo.table",
            "foobar",
            "127.0.0.1 127.0.0.2",
            "",
            "foo.single_nested",
            "foo\tbar",
            "cool\tcool2",
        ]

        for i, line in enumerate(lines):
            assert line in output[i]

    def test_print_subtable_single(
        self, mock_cli, get_operation_for_subtable_test
    ):
        output = io.StringIO()

        mock_cli.output_handler.mode = OutputMode.delimited
        mock_cli.output_handler.single_table = True

        mock_data = {
            "table": [{"foo": "cool", "bar": 12345}],
            "foo": {
                "single_nested": {"foo": "cool", "bar": "cool2"},
                "table": [{"foobar": ["127.0.0.1", "127.0.0.2"]}],
            },
            "foobar": "wow",
        }

        mock_cli.output_handler.print_response(
            get_operation_for_subtable_test.response_model,
            data=[mock_data],
            to=output,
        )

        output = output.getvalue().splitlines()

        lines = [
            "foo.single_nested.foo\tfoo.single_nested.bar\tfoobar",
            "cool\tcool2\twow",
        ]

        for i, line in enumerate(lines):
            assert line in output[i]

    def test_print_subtable_with_selection(
        self, mock_cli, get_operation_for_subtable_test
    ):
        output = io.StringIO()

        mock_cli.output_handler.mode = OutputMode.table
        mock_cli.output_handler.tables = ["foo.table", "foo.single_nested"]

        mock_data = {
            "table": [{"foo": "cool", "bar": 12345}],
            "foo": {
                "single_nested": {"foo": "cool", "bar": "cool2"},
                "table": [{"foobar": ["127.0.0.1", "127.0.0.2"]}],
            },
            "foobar": "wow",
        }

        mock_cli.output_handler.print_response(
            get_operation_for_subtable_test.response_model,
            data=[mock_data],
            to=output,
        )

        output = output.getvalue().splitlines()

        lines = [
            "foo.table",
            "┌──────────────────────┐",
            "│ foobar               │",
            "├──────────────────────┤",
            "│ 127.0.0.1, 127.0.0.2 │",
            "└──────────────────────┘",
            "foo.single_nested",
            "┌───────┬───────┐",
            "│ foo   │ bar   │",
            "├───────┼───────┤",
            "│ cool  │ cool2 │",
            "└───────┴───────┘",
        ]

        for i, line in enumerate(lines):
            assert line in output[i]

    def test_format_nested_field(
        self, mock_cli, get_operation_for_subtable_test
    ):
        output = io.StringIO()

        mock_cli.output_handler.mode = OutputMode.delimited
        mock_cli.output_handler.single_table = True
        mock_cli.output_handler.columns = "foo.single_nested.bar"

        mock_data = {
            "table": [{"foo": "cool", "bar": 12345}],
            "foo": {
                "single_nested": {"foo": "cool", "bar": "cool2"},
                "table": [{"foobar": ["127.0.0.1", "127.0.0.2"]}],
            },
            "foobar": "wow",
        }

        mock_cli.output_handler.print_response(
            get_operation_for_subtable_test.response_model,
            data=[mock_data],
            to=output,
        )

        output = output.getvalue().splitlines()

        lines = [
            "foo.single_nested.bar",
            "cool2",
        ]

        for i, line in enumerate(lines):
            assert line in output[i]
