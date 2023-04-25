"""
Handles formatting the output of commands used in Linode CLI
"""
import json
import sys
from enum import Enum
from sys import stdout

from rich import box
from rich import print as rprint
from rich.table import Table
from rich.text import Text


class OutputMode(Enum):
    """
    Enum for output modes
    """

    table = 1
    delimited = 2
    json = 3
    markdown = 4


class OutputHandler:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """
    Handles formatting the output of commands used in Linode CLI
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        mode=OutputMode.table,
        delimiter="\t",
        headers=True,
        pretty_json=False,
        columns=None,
        disable_truncation=False,
        truncation_length=64,
        suppress_warnings=False,
    ):
        self.mode = mode
        self.delimiter = delimiter
        self.pretty_json = pretty_json
        self.headers = headers
        self.columns = columns
        self.disable_truncation = disable_truncation
        self.truncation_length = truncation_length
        self.suppress_warnings = suppress_warnings

        # Used to track whether a warning has already been printed
        self.has_warned = False

    def print(
        self, response_model, data, title=None, to=stdout, columns=None
    ):  # pylint: disable=too-many-arguments
        """
        :param response_model: The Model corresponding to this response
        :type response_model: ResponseModel
        :param data: The data to display
        :type data: list[str] or list[dict]
        :param title: The title to display on a table
        :type title: str or None
        :param to: Where to print output to
        :type to: stdout, stderr or file
        :param columns: The columns to display
        :type columns: list[str]
        """

        # We need to use lambdas here since we don't want unused function params
        output_mode_to_func = {
            OutputMode.table: lambda: self._table_output(
                header, data, columns, title, to
            ),
            OutputMode.delimited: lambda: self._delimited_output(
                header, data, columns, to
            ),
            OutputMode.json: lambda: self._json_output(header, data, to),
            OutputMode.markdown: lambda: self._markdown_output(
                header, data, columns, to
            ),
        }

        if columns is None:
            columns = self._get_columns(response_model)
            header = [c.column_name for c in columns]
        else:
            header = columns

        if self.mode not in output_mode_to_func:
            raise RuntimeError(f"Unknown output mode: {self.mode}")

        output_mode_to_func[self.mode]()

    def _get_columns(self, response_model):
        """
        Based on the configured columns, returns columns from a response model
        """
        if self.columns is None:
            columns = [
                attr
                for attr in sorted(
                    response_model.attrs, key=lambda c: c.display
                )
                if attr.display
            ]
        elif self.columns == "*":
            columns = list(response_model.attrs)
        else:
            columns = []
            for col in self.columns.split(","):
                for attr in response_model.attrs:
                    if attr.column_name == col:
                        response_model.attrs.remove(attr)
                        columns.append(attr)
                        continue

        if not columns:
            # either they selected nothing, or the model wasn't setup for CLI
            # display - either way, display everything
            columns = response_model.attrs

        return columns

    def _table_output(
        self, header, data, columns, title, to
    ):  # pylint: disable=too-many-arguments
        """
        Pretty-prints data in a table
        """
        content = self._build_output_content(
            data,
            columns,
            header=header,
            value_transform=lambda attr, v: self._attempt_truncate_value(
                attr.render_value(v)
            ),
        )

        tab = Table(*content[0], header_style="", box=box.SQUARE)
        for row in content[1:]:
            row = [Text.from_ansi(item) for item in row]
            tab.add_row(*row)

        if title is not None:
            tab.title = title

        if not self.headers:
            tab.show_header = False

        rprint(tab, file=to)

    def _delimited_output(self, header, data, columns, to):
        """
        Prints data in delimited format with the given delimiter
        """
        content = self._build_output_content(
            data,
            columns,
            header=header,
            value_transform=lambda attr, v: attr.get_string(v),
        )

        for row in content:
            print(self.delimiter.join(row), file=to)

    def _json_output(self, header, data, to):
        """
        Prints data in JSON format
        """
        content = []
        if len(data) and isinstance(data[0], dict):  # we got delimited json in
            # parse down to the value we display
            for row in data:
                content.append(self._select_json_elements(header, row))
        else:  # this is a list
            for row in data:
                content.append(dict(zip(header, row)))

        print(
            json.dumps(
                content,
                indent=2 if self.pretty_json else None,
                sort_keys=self.pretty_json,
            ),
            file=to,
        )

    @staticmethod
    def _select_json_elements(keys, json_res):
        """
        Returns a dict filtered down to include only the selected keys.  Walks
        paths to handle nested dicts
        """
        ret = {}
        for k, v in json_res.items():
            if k in keys:
                ret[k] = v
            elif isinstance(v, dict):
                v = OutputHandler._select_json_elements(keys, v)
                if v:
                    ret[k] = v
        return ret

    def _markdown_output(self, header, data, columns, to):
        """
        Pretty-prints data in a Markdown-formatted table.  This uses github's
        flavor of Markdown
        """
        content = self._build_output_content(
            data,
            columns,
            value_transform=lambda attr, v: self._attempt_truncate_value(
                attr.render_value(v, colorize=False)
            ),
        )

        if header:
            print("| " + " | ".join([str(c) for c in header]) + " |", file=to)
            print("|---" * len(header) + "|", file=to)

        for row in content:
            print("| " + " | ".join([str(c) for c in row]) + " |", file=to)

    def _build_output_content(
        self,
        data,
        columns,
        header=None,
        value_transform=lambda attr, model: model,
    ):
        """
        Returns the `content` to be displayed by the corresponding output function.
        `value_transform` allows functions to specify how each value should be formatted.
        """

        content = []

        if self.headers and header is not None:
            content = [header]

        # We're not using models here
        # We won't apply transforms here since no formatting is being applied
        if isinstance(columns[0], str):
            return content + data

        for model in data:
            content.append([value_transform(attr, model) for attr in columns])

        return content

    def _attempt_truncate_value(self, value):
        if self.disable_truncation:
            return value

        if not isinstance(value, str):
            value = str(value)

        if len(value) < self.truncation_length:
            return value

        if not self.suppress_warnings and not self.has_warned:
            print(
                "Certain values in this output have been truncated. "
                "To disable output truncation, use --no-truncation. "
                "Alternatively, use the --json or --text output modes, "
                "or disable warnings using --suppress-warnings.",
                file=sys.stderr,
            )
            self.has_warned = True

        return f"{value[:self.truncation_length]}..."
