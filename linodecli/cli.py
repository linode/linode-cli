"""
Responsible for managing spec and routing commands to operations.
"""

import os
import pickle
import sys
from sys import version_info

from openapi3 import OpenAPI

from .api_request import do_request, get_all_pages
from .baked import OpenAPIOperation
from .configuration import CLIConfig
from .output import OutputHandler, OutputMode

METHODS = ("get", "post", "put", "delete")


class CLI:  # pylint: disable=too-many-instance-attributes
    """
    Responsible for loading or baking a spec and handling incoming commands
    """

    def __init__(self, version, base_url, skip_config=False):
        self.ops = {}
        self.spec = {}
        self.defaults = True  # whether to use default values for arguments
        self.pagination = True
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

    def bake(self, spec):
        """
        Generates ops and bakes them to a pickle
        """
        spec = OpenAPI(spec)
        self.spec = spec
        self.ops = {}
        ext = {
            "skip": "linode-cli-skip",
            "action": "linode-cli-action",
            "command": "linode-cli-command",
            "defaults": "linode-cli-allowed-defaults",
        }

        for path in spec.paths.values():
            command = path.extensions.get(ext["command"], "default")
            for m in METHODS:
                operation = getattr(path, m)
                if operation is None or ext["skip"] in operation.extensions:
                    continue
                action = operation.extensions.get(
                    ext["action"], operation.operationId
                )
                if not action:
                    continue
                if isinstance(action, list):
                    action = action[0]
                if command not in self.ops:
                    self.ops[command] = {}
                self.ops[command][action] = OpenAPIOperation(
                    command, operation, m, path.parameters
                )

        # hide the base_url from the spec away
        self.ops["_base_url"] = self.spec.servers[0].url
        self.ops["_spec_version"] = self.spec.info.version
        self.ops["_spec"] = self.spec

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
                    self.base_url = self.ops.pop("_base_url")
                if "_spec_version" in self.ops:
                    self.spec_version = self.ops.pop("_spec_version")
                if "_spec" in self.ops:
                    self.spec = self.ops.pop("_spec")
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

    def handle_command(self, command, action, args):
        """
        Given a command, action, and remaining kwargs, finds and executes the
        action
        """

        try:
            operation = self.find_operation(command, action)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

        if not self.pagination:
            result = get_all_pages(self, operation, args)
        else:
            result = do_request(self, operation, args).json()

        operation.process_response_json(result, self.output_handler)

        if (
            self.output_handler.mode == OutputMode.table
            and "pages" in result
            and result["pages"] > 1
        ):
            print(
                f"Page {result['page']} of {result['pages']}. "
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
