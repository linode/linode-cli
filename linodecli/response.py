"""
Classes related to parsing responses and display output from the API, based
on the OpenAPI spec.
"""
from __future__ import print_function

from colorclass import Color


class ModelAttr:
    def __init__(self, name, filterable, display, datatype, color_map=None, item_type=None):
        self.name = name
        self.value = None
        self.filterable = filterable
        self.display = display
        self.column_name = self.name.split('.')[-1]
        self.datatype = datatype
        self.color_map = color_map
        self.item_type = item_type

    def _get_value(self, model):
        """
        Returns the raw value from a model
        """
        # walk down json paths to find the value
        value = model
        for part in self.name.split('.'):
            if value is None:
                return None
            value = value[part]

        return value

    def render_value(self, model, colorize=True):
        """
        Given the model returned from the API, returns the correctly- rendered
        version of it.  This can transform text based on various rules
        configured in the spec using custom tags.  Currently supported tags:

        x-linode-cli-color
          A list of key-value pairs that represent the value, and its ideal color.
          The key "default_" is used to colorize anything that is not included.
          If omitted, no color is applied.
        """
        value = self._get_value(model)

        if isinstance(value, list):
            value = ', '.join([str(c) for c in value])

        if colorize and self.color_map is not None:
            # apply colors
            value = str(value) # just in case
            color = self.color_map.get(value) or self.color_map['default_']
            value = str(Color('{'+color+'}'+value+'{/'+color+'}'))

        if value is None:
            # don't print the word "None"
            value = ''

        return value

    def get_string(self, model):
        """
        Returns the raw value from a model, cleaning up Nones and other values
        that won't render properly as strings
        """
        value = self._get_value(model)

        if value is None:
            value = ''
        elif isinstance(value, list):
            value = ' '.join([str(c) for c in value])
        else:
            value = str(value)

        return value


class ResponseModel:
    def __init__(self, attrs, rows=None, nested_list=None):
        self.attrs = attrs
        self.rows = rows
        self.nested_list = nested_list

    def fix_json(self, json):
        """
        Takes JSON from the API and formats it into a list of rows
        """
        if self.rows:
            # take the columns as specified
            ret = []
            for c in self.rows:
                cur = json
                for part in c.split('.'):
                    cur = cur.get(part)

                if not cur:
                    # probably shouldn't happen, but ok
                    continue

                if isinstance(cur, list):
                    ret += cur
                else:
                    ret.append(cur)

            # we're good
            return ret
        elif self.nested_list:
            # we need to explode the rows into one row per entry in the nested list,
            # copying the external values
            if 'pages' in json:
                json = json['data']

            ret = []
            if not isinstance(json, list):
                json = [json]
            for cur in json:
                nlist = cur.get(self.nested_list)
                for item in nlist:
                    cobj = {k: v for k, v in cur.items() if k != self.nested_list}
                    cobj[self.nested_list] = item
                    ret.append(cobj)

            return ret
        elif 'pages' in json:
            return json['data']
        else:
            return [json]
