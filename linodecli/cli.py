"""
Responsible for managing spec and routing commands to operations.
"""

import os
import pickle
import re
import sys
from sys import version_info

from .api_request import do_request
from .configuration import CLIConfig
from .helpers import filter_markdown_links
from .operation import CLIArg, CLIOperation, URLParam
from .output import OutputHandler, OutputMode
from .response import ModelAttr, ResponseModel

METHODS = ("get", "post", "put", "delete")


class CLI:  # pylint: disable=too-many-instance-attributes
    """
    Responsible for loading or baking a spec and handling incoming commands
    """

    def __init__(self, version, base_url, skip_config=False):
        self.ops = {}
        self.spec = {}
        self.defaults = True  # whether to use default values for arguments
        self.page = 1
        self.page_size = 100
        self.debug_request = False
        self.version = version
        self.base_url = base_url
        self.spec_version = "None"
        self.suppress_warnings = False

        self.output_handler = OutputHandler()
        self.config = CLIConfig(self.base_url, skip_config=skip_config)
        self.load_baked()

    def _resolve_allOf(self, node):
        """
        Given the contents of an "allOf" node, returns the entire dct having parsed
        all refs and combined all other nodes.

        :param node: The contents of an 'allOf'
        :type node: list
        """
        ret = {}

        for cur in node:
            data = cur
            if "$ref" in cur:
                data = self._resolve_ref(cur["$ref"])
            props = {}
            if "properties" in data:
                props = data["properties"]
            elif "$ref" in cur and "/properties/" in cur["$ref"]:
                # if we referenced a property, we got a property
                props = data
            else:
                print(f"Warning: Resolved empty node for {cur} in {node}")
            ret.update(props)
        return ret

    def _resolve_ref(self, ref):
        """
        Resolves a reference to the referenced component.

        :param ref: A reference path, like '#/components/schemas/Linode'
        :type ref: str

        :returns: The resolved reference
        :rtype: dct
        """
        path_parts = ref.split("/")[1:]
        tmp = self.spec
        for part in path_parts:
            tmp = tmp[part]

        return tmp

    def _resolve_arg_recursive(self, info):
        if "allOf" in info:
            return self._resolve_arg_recursive(
                self._resolve_allOf(info["allOf"])
            )

        if "$ref" in info:
            return self._resolve_arg_recursive(self._resolve_ref(info["$ref"]))

        return info

    def _parse_args(
        self, node, prefix=None, args=None
    ):  # pylint: disable=too-many-branches
        """
        Given a node in a requestBody, parses out the properties and returns the
        CLIArg info
        """
        if args is None:
            args = {}
        if prefix is None:
            prefix = []

        for arg, info in node.items():
            read_only = info.get("readOnly")

            info = self._resolve_arg_recursive(info)

            # We want to apply the top-level read-only value to this argument if necessary
            if read_only:
                info["readOnly"] = read_only

            if "properties" in info:
                self._parse_args(
                    info["properties"], prefix=prefix + [arg], args=args
                )
                continue  # we can't edit this level of the tree
            if info.get("readOnly"):
                continue
            if "$ref" in info:
                info = self._resolve_ref(info["$ref"])
            path = ".".join(prefix + [arg])
            args[path] = {
                "type": info.get("type") or "string",
                "desc": info.get("description") or "",
                "name": arg,
                "format": info.get(
                    "x-linode-cli-format", info.get("format", None)
                ),
            }

            # if this is coming in as json, stop here
            if args[path]["format"] == "json":
                args[path]["type"] = "object"
                continue

            # handle input lists
            if args[path]["type"] == "array" and "items" in info:
                items = info["items"]

                if "allOf" in items:
                    # if items contain an "allOf", parse it down and format it
                    # as is expected here
                    items = self._resolve_allOf(items["allOf"])
                    items = {"type": "object", "items": items}
                if "$ref" in items:
                    # if it's just a ref, parse that out too
                    items = self._resolve_ref(items["$ref"])

                args[path]["item_type"] = items["type"]

                if (
                    items["type"] == "object"
                    and "properties" in items
                    and not items.get("readOnly")
                ):
                    # this is a special case - each item has its own properties
                    # that we need to capture separately
                    item_args = self._parse_args(
                        items["properties"], prefix=prefix + [arg]
                    )
                    for _, v in item_args.items():
                        v["list_item"] = path
                    args.update(item_args)
                    del args[path]  # remove the base element, which is junk

        return args

    def _parse_properties(self, node, prefix=None):
        """
        Given the value of a "properties" node, parses out the attributes and
        returns them as a list
        """
        if prefix is None:
            prefix = []
        attrs = []
        for name, info in node.items():
            if "properties" in info:
                attrs += self._parse_properties(
                    info["properties"], prefix + [name]
                )
            else:
                item_type = None
                item_container = info.get("items")
                if item_container:
                    item_type = item_container.get("type")
                attrs.append(
                    ModelAttr(
                        ".".join(prefix + [name]),
                        info.get("x-linode-filterable") or False,
                        info.get("x-linode-cli-display") or False,
                        info.get("type") or "string",
                        color_map=info.get("x-linode-cli-color"),
                        item_type=item_type,
                    )
                )

        return attrs

    def bake(
        self, spec
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """
        Generates ops and bakes them to a pickle
        """
        self.spec = spec
        self.ops = {}
        default_servers = [c["url"] for c in spec["servers"]]

        for path, data in self.spec[  # pylint: disable=too-many-nested-blocks
            "paths"
        ].items():  # pylint: disable=too-many-nested-blocks
            command = data.get("x-linode-cli-command") or "default"
            if command not in self.ops:
                self.ops[command] = {}

            params = []
            if "parameters" in data:
                for info in data["parameters"]:
                    if "$ref" in info:
                        info = self._resolve_ref(info["$ref"])
                    params.append(
                        URLParam(info["name"], info["schema"]["type"])
                    )
            for m in METHODS:
                if m in data:
                    if data[m].get("x-linode-cli-skip"):
                        # some actions aren't available to the CLI - skip them
                        continue

                    action = data[m].get("x-linode-cli-action") or data[m].get(
                        "operationId"
                    )

                    if action is None:
                        print(f"warn: no operationId for {m.upper()} {path}")
                        continue

                    action_aliases = None

                    if isinstance(action, list):
                        if len(action) < 1:
                            print(f"warn: empty list for action {m.upper()}")
                            continue

                        action_aliases = action[1:]
                        action = action[0]

                    summary = (
                        filter_markdown_links(data[m].get("summary")) or ""
                    )

                    # Resolve the documentation URL
                    docs_url = None
                    tags = data[m].get("tags")
                    if tags is not None and len(tags) > 0 and len(summary) > 0:
                        tag_path = self._flatten_url_path(tags[0])
                        summary_path = self._flatten_url_path(summary)
                        docs_url = f"https://www.linode.com/docs/api/{tag_path}/#{summary_path}"

                    use_servers = (
                        [c["url"] for c in data[m]["servers"]]
                        if "servers" in data[m]
                        else default_servers
                    )

                    args = {}
                    required_fields = []
                    allowed_defaults = None
                    if m in ("post", "put") and "requestBody" in data[m]:
                        allowed_defaults = data[m]["requestBody"].get(
                            "x-linode-cli-allowed-defaults", None
                        )

                        if (
                            "application/json"
                            in data[m]["requestBody"]["content"]
                        ):
                            body_schema = data[m]["requestBody"]["content"][
                                "application/json"
                            ]["schema"]

                            if "required" in body_schema:
                                required_fields = body_schema["required"]

                            if "allOf" in body_schema:
                                body_schema = self._resolve_allOf(
                                    body_schema["allOf"]
                                )
                            if "required" in body_schema:
                                required_fields += body_schema["required"]
                            if "$ref" in body_schema:
                                body_schema = self._resolve_ref(
                                    body_schema["$ref"]
                                )
                            if "required" in body_schema:
                                required_fields += body_schema["required"]
                            if "properties" in body_schema:
                                body_schema = body_schema["properties"]
                            if "required" in body_schema:
                                required_fields += body_schema["required"]

                            args = self._parse_args(body_schema, args={})

                    response_model = None
                    if (
                        "200" in data[m]["responses"]
                        and "application/json"
                        in data[m]["responses"]["200"]["content"]
                    ):
                        resp_con = data[m]["responses"]["200"]["content"][
                            "application/json"
                        ]["schema"]

                        if (
                            "x-linode-cli-use-schema"
                            in data[m]["responses"]["200"]["content"][
                                "application/json"
                            ]
                        ):
                            # this body is atypical, and defines its own columns
                            # using this schema instead of the normal one.  This
                            # is usually pairs with x-linode-cli-rows so to handle
                            # endpoints that returns irregularly formatted data
                            resp_con = data[m]["responses"]["200"]["content"][
                                "application/json"
                            ]["x-linode-cli-use-schema"]

                        if "$ref" in resp_con:
                            resp_con = self._resolve_ref(resp_con["$ref"])
                        if "allOf" in resp_con:
                            resp_con.update(
                                self._resolve_allOf(resp_con["allOf"])
                            )
                        # handle pagination envelope
                        if (
                            "properties" in resp_con
                            and "pages" in resp_con["properties"]
                        ):
                            resp_con = resp_con["properties"]
                        if "pages" in resp_con and "data" in resp_con:
                            if "$ref" in resp_con["data"]["items"]:
                                resp_con = self._resolve_ref(
                                    resp_con["data"]["items"]["$ref"]
                                )
                            else:
                                resp_con = resp_con["data"]["items"]

                        attrs = []
                        if "properties" in resp_con:
                            attrs = self._parse_properties(
                                resp_con["properties"]
                            )
                            # maybe we have special columns?
                            rows = (
                                data[m]["responses"]["200"]["content"][
                                    "application/json"
                                ].get("x-linode-cli-rows")
                                or None
                            )
                            nested_list = (
                                data[m]["responses"]["200"]["content"][
                                    "application/json"
                                ].get("x-linode-cli-nested-list")
                                or None
                            )
                            response_model = ResponseModel(
                                attrs, rows=rows, nested_list=nested_list
                            )

                    cli_args = []

                    for arg, info in args.items():
                        new_arg = CLIArg(
                            info["name"],
                            info["type"],
                            filter_markdown_links(
                                info["desc"].split(".")[0] + "."
                            ),
                            arg,
                            info["format"],
                            list_item=info.get("list_item"),
                        )

                        if arg in required_fields:
                            new_arg.required = True

                        # handle arrays
                        if "item_type" in info:
                            new_arg.arg_item_type = info["item_type"]
                        cli_args.append(new_arg)

                    # looks for param names that will be obscured by args
                    # clone the params since they're shared by all methods in this
                    # path, and we only want to modify this method's params
                    use_params = [c.clone() for c in params]
                    use_path = path
                    for p in use_params:
                        if p.name in args:
                            # or (m == 'get' and p.name in model_attrs):
                            # if we found a parameter name that is also and argument name
                            # append an underscore to both the parameter name and the
                            # parameter name in the URL
                            use_path = use_path.replace(
                                "{" + p.name + "}", "{" + p.name + "_}"
                            )
                            p.name += "_"

                    self.ops[command][action] = CLIOperation(
                        command,
                        action,
                        m,
                        use_path,
                        summary,
                        cli_args,
                        response_model,
                        use_params,
                        use_servers,
                        docs_url=docs_url,
                        allowed_defaults=allowed_defaults,
                        action_aliases=action_aliases,
                    )

        # remove any empty commands (those that have no actions)
        to_remove = []
        for command, actions in self.ops.items():
            if len(actions) == 0:
                to_remove.append(command)

        for command in to_remove:
            del self.ops[command]

        # hide the base_url from the spec away
        self.ops["_base_url"] = spec["servers"][0]["url"]
        self.ops["_spec_version"] = spec["info"]["version"]

        # finish the baking
        data_file = self._get_data_file()
        with open(data_file, "wb") as f:
            pickle.dump(self.ops, f)

    def load_baked(self):
        """
        Loads a baked spec representation from a baked pickle
        """
        data_file = self._get_data_file()
        data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), data_file
        )
        if os.path.exists(data_path):
            with open(data_path, "rb") as f:
                self.ops = pickle.load(f)
                if "_base_url" in self.ops:
                    self.base_url = self.ops["_base_url"]
                    del self.ops["_base_url"]
                if "_spec_version" in self.ops:
                    self.spec_version = self.ops["_spec_version"]
                    del self.ops["_spec_version"]
        else:
            print(
                "No spec baked.  Please bake by calling this script as follows:"
            )
            print("  python3 gen_cli.py bake /path/to/spec")
            self.ops = None  # this signals __init__.py to give up

    def _get_data_file(self):
        """
        Returns the name of the baked data file this program wants.  This is in
        part based on python version.
        """
        return f"data-{version_info[0]}"

    @staticmethod
    def _flatten_url_path(tag):
        new_tag = tag.lower()
        new_tag = re.sub(r"[^a-z ]", "", new_tag).replace(" ", "-")
        return new_tag

    def handle_command(self, command, action, args):
        """
        Given a command, action, and remaining kwargs, finds and executes the
        action
        """
        if (command, action) in [
            ("linodes", "ips-list"),
            ("firewalls", "rules-list"),
        ] and "--json" not in args:
            print(
                "This output contains a nested structure that may not properly "
                + "be displayed by linode-cli.",
                "A fix is currently on the roadmap but has not yet been implemented.",
                "Please use --json for endpoints like this in the meantime.",
                file=sys.stderr,
            )

        try:
            operation = self.find_operation(command, action)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

        result = do_request(self, operation, args)

        operation.process_response_json(result.json(), self.output_handler)

        if (
            self.output_handler.mode == OutputMode.table
            and "pages" in result.json()
            and result.json()["pages"] > 1
        ):
            print(
                f"Page {result.json()['page']} of {result.json()['pages']}. "
                "Call with --page [PAGE] to load a different page."
            )

    def configure(self):
        """
        Reconfigure the application
        """
        self.config.configure()

    def call_operation(self, command, action, args=None, filters=None):
        """
        This function is used in plugins to retrieve the result of CLI operations
        in JSON format.  This uses the configured user of the CLI.

        :param filters: The X-Filter header to include in the request.  This overrides
                        whatever is passed into to command as filters.
        :type filters: dict
        """
        if args is None:
            args = []
        if command not in self.ops or action not in self.ops[command]:
            raise ValueError(f"Unknown command/action {command}/{action}")

        operation = self.ops[command][action]

        result = do_request(
            self,
            operation,
            args,
            filter_header=filters,
            skip_error_handling=True,
        )

        return result.status_code, result.json()

    def find_operation(self, command, action):
        """
        Finds the corresponding operation for the given command and action.
        """
        if command not in self.ops:
            raise ValueError(f"Command not found: {command}")

        command_dict = self.ops[command]

        if action in command_dict:
            return command_dict[action]

        # Find the matching alias
        for op in command_dict.values():
            if action in op.action_aliases:
                return op

        # Fail if no matching alias was found
        raise ValueError(f"No action {action} for command {command}")
