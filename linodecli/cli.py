"""
Responsible for managing spec and routing commands to operations.
"""

import contextlib
import json
import os
import pickle
import sys
from json import JSONDecodeError
from logging import getLogger
from sys import version_info
from typing import IO, Any, ContextManager, Dict

import requests
import yaml
from openapi3 import OpenAPI

from linodecli.api_request import do_request, get_all_pages
from linodecli.baked import OpenAPIOperation
from linodecli.configuration import CLIConfig
from linodecli.exit_codes import ExitCodes
from linodecli.output.output_handler import OutputHandler, OutputMode

METHODS = ("get", "post", "put", "delete")

logger = getLogger(__name__)


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

    def bake(self, spec_location: str, save: bool = True):
        """
        Generates ops and bakes them to a pickle.

        :param spec_location: The URL or file path of the OpenAPI spec to parse.
        :param save: Whether the pickled operations should be saved to a file.
                     This is primarily intended for unit testing.
        """

        try:
            logger.debug("Loading and parsing OpenAPI spec: %s", spec_location)
            spec = self._load_openapi_spec(spec_location)
        except Exception as e:
            print(f"Failed to load spec: {e}")
            sys.exit(ExitCodes.REQUEST_FAILED)

        self.spec = spec
        self.ops = {}
        ext = {
            "skip": "linode-cli-skip",
            "action": "linode-cli-action",
            "command": "linode-cli-command",
            "defaults": "linode-cli-allowed-defaults",
        }

        for path in spec.paths.values():
            command = path.extensions.get(ext["command"], None)

            for m in METHODS:
                operation = getattr(path, m)

                if operation is None:
                    continue

                operation_log_fmt = f"{m.upper()} {path.path[-1]}"

                logger.debug(
                    "%s: Attempting to generate command for operation",
                    operation_log_fmt,
                )

                if ext["skip"] in operation.extensions:
                    logger.debug(
                        "%s: Skipping operation due to x-%s extension",
                        operation_log_fmt,
                        ext["skip"],
                    )
                    continue

                # We don't do this in the parent loop because certain paths
                # may only have skipped operations
                if command is None:
                    raise KeyError(
                        f"{operation_log_fmt}: Missing x-{ext['command']} extension"
                    )

                action = operation.extensions.get(ext["action"], None)

                if action is None:
                    action = operation.operationId
                    logger.info(
                        "%s: Using operationId (%s) as action because "
                        "%s extension is not specified",
                        operation_log_fmt,
                        action,
                        ext["action"],
                    )

                if not action:
                    logger.warning(
                        "%s: Skipping operation due to unresolvable action",
                        operation_log_fmt,
                    )
                    continue

                if isinstance(action, list):
                    action = action[0]

                if command not in self.ops:
                    self.ops[command] = {}

                operation = OpenAPIOperation(
                    command, operation, m, path.parameters
                )

                logger.debug(
                    "%s %s: Successfully built command for operation: "
                    "command='%s %s'; summary='%s'; paginated=%s; num_args=%s; num_attrs=%s",
                    operation.method.upper(),
                    operation.url_path,
                    operation.command,
                    operation.action,
                    operation.summary.rstrip("."),
                    operation.response_model
                    and operation.response_model.is_paginated,
                    len(operation.args),
                    len(operation.attrs),
                )

                self.ops[command][action] = operation

        # hide the base_url from the spec away
        self.ops["_base_url"] = self.spec.servers[0].url
        self.ops["_spec_version"] = self.spec.info.version
        self.ops["_spec"] = self.spec

        # finish the baking
        data_file = self._get_data_file()

        with open(data_file, "wb") if save else os.devnull as f:
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
                "No spec baked.  Please bake by calling this script as follows:",
                file=sys.stderr,
            )
            print("  python3 gen_cli.py bake /path/to/spec", file=sys.stderr)
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
            sys.exit(ExitCodes.REQUEST_FAILED)

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
            # Check that the passed command is not an alias before raising an error
            if command in self.config.get_custom_aliases().keys():
                command = self.config.get_custom_aliases()[command]
            else:
                raise ValueError(f"Command not found: {command}")

        command_dict = self.ops[command]

        if action in command_dict:
            return command_dict[action]

        # Find the matching alias
        for op in command_dict.values():
            if action in op.action_aliases:
                return op

        # Fail if no matching alias was found
        raise ValueError(f"Action not found for command {command}: {action}")

    @property
    def user_agent(self) -> str:
        """
        Returns the User-Agent to use when making API requests.
        """
        return (
            f"linode-cli/{self.version} "
            f"linode-api-docs/{self.spec_version} "
            f"python/{version_info[0]}.{version_info[1]}.{version_info[2]}"
        )

    @staticmethod
    def _load_openapi_spec(spec_location: str) -> OpenAPI:
        """
        Attempts to load the raw OpenAPI spec (YAML or JSON) at the given location.

        :param spec_location: The location of the OpenAPI spec.
                              This can be a local path or a URL.

        :returns: A tuple containing the loaded OpenAPI object and the parsed spec in
                  dict format.
        """

        with CLI._get_spec_file_reader(spec_location) as f:
            parsed = CLI._parse_spec_file(f)

        return OpenAPI(parsed)

    @staticmethod
    @contextlib.contextmanager
    def _get_spec_file_reader(
        spec_location: str,
    ) -> ContextManager[IO]:
        """
        Returns a reader for an OpenAPI spec file from the given location.

        :param spec_location: The location of the OpenAPI spec.
                      This can be a local path or a URL.

        :returns: A context manager yielding the spec file's reader.
        """

        # Case for local file
        local_path = os.path.expanduser(spec_location)
        if os.path.exists(local_path):
            f = open(local_path, "r", encoding="utf-8")

            try:
                yield f
            finally:
                f.close()

            return

        # Case for remote file
        resp = requests.get(spec_location, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to GET {spec_location}")

        # We need to access the underlying urllib
        # response here so we can return a reader
        # usable in yaml.safe_load(...) and json.load(...)
        resp.raw.decode_content = True

        try:
            yield resp.raw
        finally:
            resp.close()

    @staticmethod
    def _parse_spec_file(reader: IO) -> Dict[str, Any]:
        """
        Parses the given file reader into a dict and returns a dict.

        :param reader: A reader for a YAML or JSON file.

        :returns: The parsed file.
        """

        errors = []

        try:
            return yaml.safe_load(reader)
        except yaml.YAMLError as err:
            errors.append(str(err))

        try:
            return json.load(reader)
        except JSONDecodeError as err:
            errors.append(str(err))

        raise ValueError(f"Failed to parse spec file: {'; '.join(errors)}")
