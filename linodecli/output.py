from __future__ import print_function

from enum import Enum
import json
from terminaltables import SingleTable
from sys import stdout


class OutputMode(Enum):
    table=1
    delimited=2
    json=3
    markdown=4


class OutputHandler:
    def __init__(self, mode=OutputMode.table, delimiter='\t', headers=True,
                 pretty_json=False, columns=None):
        self.mode = mode
        self.delimiter = delimiter
        self.pretty_json = pretty_json
        self.headers = headers
        self.columns = columns

    def print(self, response_model, data, title=None, to=stdout, columns=None):
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
        if columns is None:
            columns = self._get_columns(response_model)
            header = [c.column_name for c in columns]
        else:
            header = columns

        if self.mode == OutputMode.table:
            self._table_output(header, data, columns, title, to)
        elif self.mode == OutputMode.delimited:
            self._delimited_output(header, data, columns, to)
        elif self.mode == OutputMode.json:
            self._json_output(header, data, to)
        elif self.mode == OutputMode.markdown:
            self._markdown_output(header, data, columns, to)

    def _get_columns(self, response_model):
        """
        Based on the configured columns, returns columns from a response model
        """
        if self.columns is None:
            columns = [attr for attr in sorted(response_model.attrs, key=lambda c: c.display) if attr.display]
        elif self.columns == '*':
            columns = [attr for attr in response_model.attrs]
        else:
            columns = []
            for col in self.columns.split(','):
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

    def _table_output(self, header, data, columns, title, to):
        """
        Pretty-prints data in a table
        """
        content = []

        if isinstance(columns[0], str):
            content=data
        else:
            for model in data:
                content.append([attr.render_value(model) for attr in columns])

        if self.headers:
            content = [header]+content

        tab = SingleTable(content)

        if title is not None:
            tab.title=title

        if not self.headers:
            tab.inner_heading_row_border = False

        print(tab.table, file=to)

    def _delimited_output(self, header, data, columns, to):
        """
        Prints data in delimited format with the given delimiter
        """
        content=[]

        if isinstance(columns[0], str):
            content = data
        else:
            for model in data:
                content.append([attr.get_string(model) for attr in columns])

        if self.headers:
            content=[header]+content

        for row in content:
            print(self.delimiter.join(row), file=to)

    def _json_output(self, header, data, to):
        """
        Prints data in JSON format
        """
        content = []
        if len(data) and isinstance(data[0], dict): # we got delimited json in
            # parse down to the value we display
            for row in data:
                content.append(self._select_json_elements(header, row))
        else: # this is a list
            for row in data:
                content.append({h: v for h, v in zip(header, row)})

        print(json.dumps(content, indent=2 if self.pretty_json else None,
                         sort_keys=self.pretty_json), file=to)

    def _select_json_elements(self, keys, json):
        """
        Returns a dict filtered down to include only the selected keys.  Walks
        paths to handle nested dicts
        """
        ret = {}
        for k, v in json.items():
            if k in keys:
                ret[k] = v
            elif isinstance(v, dict):
                v = self._select_json_elements(keys, v)
                if v:
                    ret[k] = v
        return ret

    def _markdown_output(self, header, data, columns, to):
        """
        Pretty-prints data in a Markdown-formatted table.  This uses github's
        flavor of Markdown
        """
        content = []

        if isinstance(columns[0], str):
            content=data
        else:
            for model in data:
                content.append([attr.render_value(model, colorize=False) for attr in columns])

        if header:
            print('| ' + ' | '.join([str(c) for c in header]) + ' |')
            print('|---' * len(header) + '|')

        for row in content:
            print('| ' + ' | '.join([str(c) for c in row]) + ' |')
