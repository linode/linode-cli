import contextlib
import io

from rich import box
from rich import print as rprint
from rich.table import Table

from linodecli import ModelAttr, OutputMode, ResponseModel


class TestOutputHandler:
    """
    Unit tests for linodecli.output
    """

    def test_markdown_output_columns(self, mock_cli):
        output = io.StringIO()

        output_handler = mock_cli.output_handler

        output_handler._markdown_output(
            ["very cool header", "wow"],
            [["foo", "bar"], ["oof", "rab"]],
            ["1", "2"],
            output,
        )

        assert (
            output.getvalue() == "| very cool header | wow |\n"
            "|---|---|\n"
            "| foo | bar |\n"
            "| oof | rab |\n"
        )

    def test_markdown_output_models(self, mock_cli):
        output = io.StringIO()

        output_handler = mock_cli.output_handler

        output_handler._markdown_output(
            ["very cool header"],
            [{"cool": "foo"}, {"cool": "bar"}],
            [ModelAttr("cool", True, True, "string")],
            output,
        )

        assert (
            output.getvalue() == "| very cool header |\n"
            "|---|\n"
            "| foo |\n"
            "| bar |\n"
        )

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

    def test_delimited_output_models(self, mock_cli):
        output = io.StringIO()
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {"cool": "bar"},
        ]
        columns = [ModelAttr("cool", True, True, "string")]

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
        tab = Table("h1", "h2", header_style="", box=box.SQUARE)
        for row in [["foo", "bar"], ["oof", "rab"]]:
            tab.add_row(*row)
        tab.title = "cool table"
        rprint(tab, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_table_output_models(self, mock_cli):
        output = io.StringIO()
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {"cool": "bar"},
        ]
        columns = [ModelAttr("cool", True, True, "string")]

        mock_cli.output_handler._table_output(
            header, data, columns, "cool table", output
        )

        mock_table = io.StringIO()
        tab = Table("h1", header_style="", box=box.SQUARE)
        for row in [["foo"], ["bar"]]:
            tab.add_row(*row)
        tab.title = "cool table"
        rprint(tab, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_table_output_models_no_headers(self, mock_cli):
        mock_cli.output_handler.headers = False

        output = io.StringIO()
        header = ["h1"]
        data = [
            {
                "cool": "foo",
            },
            {"cool": "bar"},
        ]
        columns = [ModelAttr("cool", True, True, "string")]

        mock_cli.output_handler._table_output(
            header, data, columns, "cool table", output
        )

        mock_table = io.StringIO()
        tab = Table(header_style="", show_header=False, box=box.SQUARE)
        for row in [["foo"], ["bar"]]:
            tab.add_row(*row)
        tab.title = "cool table"
        rprint(tab, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_get_columns_from_model(self, mock_cli):
        output_handler = mock_cli.output_handler

        response_model = ResponseModel(
            [
                ModelAttr("foo", True, True, "string"),
                ModelAttr("bar", True, False, "string"),
            ]
        )

        result = output_handler._get_columns(response_model)

        assert len(result) == 1
        assert result[0].name == "foo"

    def test_get_columns_from_model_all(self, mock_cli):
        output_handler = mock_cli.output_handler
        response_model = ResponseModel(
            [
                ModelAttr("foo", True, True, "string"),
                ModelAttr("bar", True, False, "string"),
            ]
        )

        output_handler.columns = "*"

        result = output_handler._get_columns(response_model)

        assert len(result) == 2
        assert result[0].name == "foo"
        assert result[1].name == "bar"

    def test_get_columns_from_model_select(self, mock_cli):
        output_handler = mock_cli.output_handler

        response_model = ResponseModel(
            [
                ModelAttr("foo", True, True, "string"),
                ModelAttr("bar", True, False, "string"),
                ModelAttr("test", True, False, "string"),
            ]
        )

        output_handler.columns = "foo,bar"

        result = output_handler._get_columns(response_model)

        assert len(result) == 2
        assert result[0].name == "foo"
        assert result[1].name == "bar"

    # Let's test a single print case
    def test_print(self, mock_cli):
        output = io.StringIO()

        response_model = ResponseModel(
            [
                ModelAttr("foo", True, True, "string"),
                ModelAttr("bar", True, True, "string"),
                ModelAttr("test", True, False, "string"),
            ]
        )

        mock_cli.output_handler.mode = OutputMode.json

        mock_cli.output_handler.print(
            response_model,
            [{"foo": "blah", "bar": "blah2", "test": "blah3"}],
            title="cool table",
            to=output,
        )

        assert '[{"foo": "blah", "bar": "blah2"}]' in output.getvalue()

    def test_truncation(self, mock_cli):
        stderr_buf = io.StringIO()
        test_str = "x" * 80
        test_str_truncated = f"{'x' * 64}..."

        with contextlib.redirect_stderr(stderr_buf):
            result = mock_cli.output_handler._attempt_truncate_value(test_str)

        assert "truncation" in stderr_buf.getvalue()
        assert result == test_str_truncated

        # --suppress-warnings
        # Faster than flushing apparently
        stderr_buf = io.StringIO()
        mock_cli.output_handler.suppress_warnings = True

        with contextlib.redirect_stderr(stderr_buf):
            result = mock_cli.output_handler._attempt_truncate_value(test_str)

        assert "truncation" not in stderr_buf
        assert result == test_str_truncated

        # --no-truncation
        mock_cli.output_handler.disable_truncation = True

        result = mock_cli.output_handler._attempt_truncate_value(test_str)

        assert result == test_str

        # Ensure integers are properly converted
        result = mock_cli.output_handler._attempt_truncate_value(12345)

        assert result == "12345"
        assert isinstance(result, str)

    def test_truncated_table(self, mock_cli):
        output = io.StringIO()

        test_str = "x" * 80
        test_str_truncated = f"{'x' * 64}..."

        header = ["h1"]
        data = [
            {
                "cool": test_str,
            },
        ]
        columns = [ModelAttr("cool", True, True, "string")]

        mock_cli.output_handler._table_output(
            header, data, columns, "cool table", output
        )

        data[0]["cool"] = test_str_truncated

        mock_table = io.StringIO()
        tab = Table("h1", header_style="", box=box.SQUARE)
        tab.add_row(test_str_truncated)
        tab.title = "cool table"
        rprint(tab, file=mock_table)

        assert output.getvalue() == mock_table.getvalue()

    def test_truncated_markdown(self, mock_cli):
        test_str = "x" * 80
        test_str_truncated = f"{'x' * 64}..."

        output = io.StringIO()

        header = ["very cool header"]
        data = [
            {
                "cool": test_str,
            },
        ]
        columns = [ModelAttr("cool", True, True, "string")]

        output_handler = mock_cli.output_handler

        output_handler._markdown_output(header, data, columns, output)

        assert (
            output.getvalue() == "| very cool header |\n"
            "|---|\n"
            f"| {test_str_truncated} |\n"
        )

    def test_warn_broken_output(self, mock_cli):
        stderr_buf = io.StringIO()

        try:
            with contextlib.redirect_stderr(stderr_buf):
                mock_cli.handle_command("linodes", "ips-list", ["10"])
        except SystemExit:
            pass

        assert (
            "This output contains a nested structure that may not properly be displayed by linode-cli."
            in stderr_buf.getvalue()
        )

        try:
            with contextlib.redirect_stderr(stderr_buf):
                mock_cli.handle_command("firewalls", "rules-list", ["10"])
        except SystemExit:
            pass

        assert (
            "This output contains a nested structure that may not properly be displayed by linode-cli."
            in stderr_buf.getvalue()
        )
