"""
Handles formatting the output of commands used in Linode CLI
"""

import copy
import json
import sys
from argparse import Namespace
from enum import Enum, auto
from sys import stdout
from typing import IO, Any, Dict, List, Optional, Union, cast

from rich import box
from rich import print as rprint
from rich.console import OverflowMethod
from rich.table import Column, Table

from linodecli.baked.response import OpenAPIResponse, OpenAPIResponseAttr
from linodecli.baked.util import get_terminal_keys


class OutputMode(Enum):
    """
    Enum for output modes
    """

    table = auto()
    delimited = auto()
    json = auto()
    markdown = auto()
    ascii_table = auto()


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
        suppress_warnings=False,
        column_width=None,
        single_table=False,
        tables=None,
    ):
        self.mode = mode
        self.delimiter = delimiter
        self.pretty_json = pretty_json
        self.headers = headers
        self.columns = columns
        self.suppress_warnings = suppress_warnings

        self.disable_truncation = disable_truncation
        self.column_width = column_width
        self.single_table = single_table
        self.tables = tables

        # Used to track whether a warning has already been printed
        self.has_warned = False

    def print(
        self,
        data: List[Union[str, dict]],
        columns: List[Union[str, OpenAPIResponseAttr]],
        title: Optional[str] = None,
        to: IO[str] = stdout,
    ):  # pylint: disable=too-many-arguments
        """
        :param data: The data to display
        :type data: list[str] or list[dict]
        :param title: The title to display on a table
        :type title: Optional[str]
        :param to: Where to print output to
        :type to: stdout, stderr or file
        :param columns: The columns to display
        :type columns: Optional[List[str]]
        """

        # We need to use lambdas here since we don't want unused function params
        output_mode_to_func = {
            OutputMode.table: lambda: self._table_output(
                header, data, columns, title, to
            ),
            OutputMode.ascii_table: lambda: self._table_output(
                header, data, columns, title, to, box_style=box.ASCII
            ),
            OutputMode.delimited: lambda: self._delimited_output(
                header, data, columns, to, title=title
            ),
            OutputMode.json: lambda: self._json_output(header, data, to),
            OutputMode.markdown: lambda: self._table_output(
                header, data, columns, title, to, box_style=box.MARKDOWN
            ),
        }

        if len(columns) < 1:
            raise ValueError(
                "Expected a non-zero number of columns."
                "This is always an error in the OpenAPI spec."
            )

        if isinstance(columns[0], OpenAPIResponseAttr):
            header = [c.name for c in columns]
        else:
            header = columns

        if self.mode not in output_mode_to_func:
            raise RuntimeError(f"Unknown output mode: {self.mode}")

        output_mode_to_func[self.mode]()

    def print_response(
        self,
        response_model: OpenAPIResponse,
        data: List[Union[str, dict]],
        to: IO[str] = stdout,
    ):
        """
        Handles printing responses from Linode API requests.

        :param response_model: The OpenAPI response to format this output with.
        :type response_model: OpenAPIResponse
        :param data: The API-returned data to output.
        :type data: List[Union[str, dict]]
        :param to: The IO stream to output to.
        :type to: IO[str]
        """
        attrs = copy.deepcopy(response_model.attrs)
        tables = []
        target_tables = self._get_tables(
            [None] + (response_model.subtables or [])
        )

        if (
            response_model.subtables is not None
            # We do not want to use subtables in JSON output
            and self.mode != OutputMode.json
            and not self.single_table
        ):
            for table in response_model.subtables:
                # Store these tables to be printed after the primary table
                tables.append(
                    (table, self._pop_attrs_for_subtable(attrs, table))
                )

        # Add a root table if any attributes remain
        if len(attrs) > 0:
            # The root table should always be printed first
            tables.insert(0, (None, attrs))

        for i, v in enumerate(tables):
            table_name, table_attrs = v
            if table_name not in target_tables:
                continue

            self.print(
                (
                    self._scope_data_to_subtable(data, table_name)
                    if table_name is not None
                    else data
                ),
                self._get_columns(table_attrs),
                title=table_name,
                to=to,
            )

            # Print gaps between tables for delimited outputs
            if self.mode == OutputMode.delimited and i < len(tables) - 1:
                print(file=to)

    @staticmethod
    def _pop_attrs_for_subtable(
        attrs: List[OpenAPIResponseAttr], table: str
    ) -> List[OpenAPIResponseAttr]:
        """
        Pops all attributes that belong to the given subtable
        and returns them.
        """
        results = [v for v in attrs if v.name.startswith(table + ".")]

        # Drop the corresponding entries from the root attrs
        for v in results:
            attrs.remove(v)

        # Scope the attributes to root
        for v in results:
            v.name = v.name[len(table) + 1 :]
            v.nested_list_depth -= 1

        return results

    @staticmethod
    def _scope_data_to_subtable(data: List[Dict[str, Any]], table: str) -> Any:
        """
        Scopes the given JSON dictionary to the given subtable.
        """
        if len(data) == 0:
            return data

        result = data[0] if isinstance(data, list) else data

        for seg in table.split("."):
            if seg not in result:
                raise IndexError(f"Segment {seg} missing from input data")

            result = result[seg]

        return result if isinstance(result, list) else [result]

    def _get_tables(self, tables):
        """
        Returns which tables to display based on the configured columns (--format).
        """
        if self.tables is None or len(self.tables) < 1 or "*" in self.tables:
            return tables

        displayed_tables = [(v if v != "root" else None) for v in self.tables]

        result = [v for v in tables if v in displayed_tables]

        # If there is nothing to print, we should print everything
        return result if len(result) > 0 else tables

    def _get_columns(self, attrs, max_depth=1):
        """
        Based on the configured columns, returns columns from a response model
        """

        if self.columns is None:
            columns = [
                attr
                for attr in sorted(attrs, key=lambda c: c.display)
                if attr.display
            ]
        elif self.columns == "*":
            columns = list(attrs)
        else:
            columns = []
            for col in self.columns.split(","):
                for attr in attrs:
                    # Display this column if the format string
                    # matches the path of this column
                    if col == attr.name:
                        attrs.remove(attr)
                        columns.append(attr)

        if not columns:
            # either they selected nothing, or the model wasn't setup for CLI
            # display - either way, display everything
            columns = attrs

        return [
            v
            for v in columns
            # We don't want to limit the attribute depth on JSON
            # outputs since JSON can properly display nested lists.
            if self.mode == OutputMode.json or v.nested_list_depth < max_depth
        ]

    def _table_output(
        self, header, data, columns, title, to, box_style=box.SQUARE
    ):  # pylint: disable=too-many-arguments
        """
        Pretty-prints data in a table
        """
        content = self._build_output_content(
            data,
            columns,
            value_transform=lambda attr, v: str(attr.render_value(v)),
        )

        # Determine the rich overflow mode to use
        # for each column.
        overflow_mode = cast(
            OverflowMethod, "fold" if self.disable_truncation else "ellipsis"
        )

        # Convert the headers into column objects
        # so we can override the overflow method.
        header_columns = [
            Column(v, overflow=overflow_mode, max_width=self.column_width)
            for v in header
        ]

        tab = Table(
            *header_columns,
            header_style="bold",
            box=box_style,
            show_header=self.headers,
            title_justify="left",
            show_lines=True,
        )
        for row in content:
            tab.add_row(*row)

        if title is not None and self.headers:
            tab.title = title
            tab.min_width = self.column_width or len(title)

        rprint(tab, file=to)

    def _delimited_output(
        self, header, data, columns, to, title=None
    ):  # pylint: disable=too-many-arguments
        """
        Prints data in delimited format with the given delimiter
        """
        content = self._build_output_content(
            data,
            columns,
            header=header,
            value_transform=lambda attr, v: attr.get_string(v),
        )

        if title is not None and self.headers:
            print(title, file=to)

        for row in content:
            print(self.delimiter.join(row), file=to)

    def _json_output(self, header, data, to):
        """
        Prints data in JSON format
        """
        # Special handling for JSON headers.
        # We're only interested in the last part of the column name, unless the last
        # part is a dotted key. If the last part is a dotted key, include the entire dotted key.

        content = []
        if len(data) and isinstance(data[0], dict):  # we got delimited json in
            parsed_header = []
            terminal_keys = get_terminal_keys(data[0])

            for v in header:
                parts = v.split(".")
                if (
                    len(parts) >= 2
                    and ".".join([parts[-2], parts[-1]]) in terminal_keys
                ):
                    parsed_header.append(".".join([parts[-2], parts[-1]]))
                else:
                    parsed_header.append(parts[-1])

            # parse down to the value we display
            for row in data:
                content.append(self._select_json_elements(parsed_header, row))
        else:  # this is a list
            header = [v.split(".")[-1] for v in header]

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
            elif isinstance(v, list):
                results = []
                for elem in v:
                    if not isinstance(elem, dict):
                        continue

                    selected = OutputHandler._select_json_elements(keys, elem)
                    if not selected:
                        continue

                    results.append(selected)

                ret[k] = results

        return ret

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

    def configure(
        self,
        parsed: Namespace,
        suppress_warnings: bool = False,
    ):
        """
        Configure the given OutputHandler with the parsed arguments.
        """
        if parsed.text:
            self.mode = OutputMode.delimited
        elif parsed.json:
            self.mode = OutputMode.json
            self.columns = "*"
        elif parsed.markdown:
            self.mode = OutputMode.markdown
        elif parsed.ascii_table:
            self.mode = OutputMode.ascii_table

        if parsed.delimiter:
            self.delimiter = parsed.delimiter
        if parsed.pretty:
            self.mode = OutputMode.json
            self.pretty_json = True
            self.columns = "*"
        if parsed.no_headers:
            self.headers = False

        self.suppress_warnings = parsed.suppress_warnings
        self.disable_truncation = parsed.no_truncation
        self.column_width = parsed.column_width
        self.single_table = parsed.single_table
        self.tables = parsed.table

        if parsed.all_columns or parsed.all:
            if parsed.all and not suppress_warnings:
                print(
                    "WARNING: '--all' is a deprecated flag, "
                    "and will be removed in a future version. "
                    "Please consider use '--all-columns' instead.",
                    file=sys.stderr,
                )
            self.columns = "*"
        elif parsed.format:
            self.columns = parsed.format
