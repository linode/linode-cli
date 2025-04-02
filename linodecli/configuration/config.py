"""
Contains logic for loading, updating, and saving Linode CLI configurations.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

from linodecli.exit_codes import ExitCodes

from .auth import (
    _check_full_access,
    _do_get_request,
    _get_token_terminal,
    _get_token_web,
)
from .helpers import (
    _bool_input,
    _check_browsers,
    _config_get_with_default,
    _default_text_input,
    _default_thing_input,
    _get_config,
    _get_config_path,
)

ENV_TOKEN_NAME = "LINODE_CLI_TOKEN"


class CLIConfig:
    """
    Generates the necessary config for the Linode CLI
    """

    def __init__(
        self, base_url: str, username: str = None, skip_config: bool = False
    ):
        """
        Initializes a new instance of the CLIConfig class.

        :param base_url: The base URL for the Linode API.
        :type base_url: str
        :param username: (optional) The username to use for authentication. Defaults to None.
        :type: username: str
        :param skip_config: (optional) If True, skip loading the configuration file.
                            Defaults to False.
        :type skip_config: bool
        """
        self.base_url = base_url
        self.username = username
        self.config = _get_config(load=not skip_config)
        self.running_plugin = None
        self.used_env_token = False

        self._configured = False

        self.configure_with_pat = "--token" in sys.argv

        if (
            not skip_config
            and not self.config.has_option("DEFAULT", "default-user")
            and self.config.has_option("DEFAULT", "token")
        ):
            self._handle_no_default_user()

        environ_token = os.getenv(ENV_TOKEN_NAME, None)

        if (
            not self.config.has_option("DEFAULT", "default-user")
            and not skip_config
            and environ_token is None
        ):
            self.configure()
        elif environ_token is not None:
            self.used_env_token = True

    def default_username(self) -> str:
        """
        Returns the `default-user` username.

        :returns: The `default-user` username or an empty string.
        :rtype: str
        """
        return self.config.get("DEFAULT", "default-user", fallback="")

    def set_user(self, username: str):
        """
        Sets the acting username.  If this username is not in the config, this is
        an error.  This overrides the default username

        :param username: The username to set.
        :type username: str
        """
        if not self.config.has_section(username):
            print(f"User {username} is not configured!", file=sys.stderr)
            sys.exit(ExitCodes.USERNAME_ERROR)

        self.username = username

    def remove_user(self, username: str):
        """
        Removes the requested user from the config.  If the user is the default,
        this exits with error.

        :param username: The username to remove.
        :type username: str
        """
        if self.default_username() == username:
            print(
                f"Cannot remove {username} as they are the default user! You can "
                "change the default user with: `linode-cli set-user USERNAME`",
                file=sys.stderr,
            )
            sys.exit(ExitCodes.USERNAME_ERROR)

        if self.config.has_section(username):
            self.config.remove_section(username)
            self.write_config()

    def print_users(self):
        """
        Prints all users available to stdout and exits.
        """
        print("Configured Users: ")
        default_user = self.default_username()

        for sec in self.config.sections():
            if sec != "DEFAULT":
                print(f'{"*" if sec == default_user else " "}  {sec}')

        sys.exit(ExitCodes.SUCCESS)

    def set_default_user(self, username: str):
        """
        Sets the default user.  If that user isn't in the config, exits with error
        """
        if not self.config.has_section(username):
            print(f"User {username} is not configured!", file=sys.stderr)
            sys.exit(ExitCodes.USERNAME_ERROR)

        self.config.set("DEFAULT", "default-user", username)
        self.write_config()

    def get_token(self) -> str:
        """
        Returns the token for a configured user.

        :returns: The token retrieved from the environment or config.
        :rtype: str
        """
        if self.used_env_token:
            return os.getenv(ENV_TOKEN_NAME, None)

        return self.config.get(
            self.username or self.default_username(), "token", fallback=""
        )

    def get_value(self, key: str) -> Optional[Any]:
        """
        Retrieves and returns an existing config value for the current user.  This
        is intended for plugins to use instead of having to deal with figuring out
        who the current user is when accessing their config.

        .. warning::
           Plugins _MUST NOT_ set values for the user's config except through
           ``plugin_set_value`` below.

        :param key: The key to look up.
        :type key: str

        :returns: The value for that key, or None if the key doesn't exist for the
                  current user.
        :rtype: any
        """
        return self.config.get(
            self.username or self.default_username(), key, fallback=None
        )

    def get_bool(self, key: str) -> bool:
        """
        Retrieves and returns an existing config boolean for the current user.  This
        is intended for plugins to use instead of having to deal with figuring out
        who the current user is when accessing their config.

        .. warning::
           Plugins _MUST NOT_ set values for the user's config except through
           ``plugin_set_value`` below.

        :param key: The key to look up.
        :type key: str

        :returns: The boolean for that key, or False if the key doesn't exist for the
                  current user.
        :rtype: any
        """

        return self.config.getboolean(
            self.username or self.default_username(), key, fallback=False
        )

    # plugin methods - these are intended for plugins to utilize to store their
    # own persistent config information
    def plugin_set_value(self, key: str, value: Any):
        """
        Sets a new config value for a plugin for the current user.  Plugin config
        keys are set in the following format::

           plugin-{plugin_name}-{key}

        Values set with this method are intended to be retrieved with ``plugin_get_value``
        below.

        :param key: The config key to set - this is needed to retrieve the value
        :type key: str
        :param value: The value to set for this key
        :type value: any
        """
        if self.running_plugin is None:
            raise RuntimeError(
                "No running plugin to retrieve configuration for!"
            )

        username = self.username or self.default_username()
        self.config.set(username, f"plugin-{self.running_plugin}-{key}", value)

    def plugin_get_value(self, key: str) -> Optional[Any]:
        """
        Retrieves and returns a config value previously set for a plugin.  Your
        plugin should have set this value in the past.  If this value does not
        exist in the config, ``None`` is returned.  This is the only time
        ``None`` is returned, so receiving this value should be treated as
        "plugin is not configured."

        :param key: The key of the value to return
        :type key: str

        :returns: The value for this plugin for this key, or None if not set
        :rtype: any
        """
        if self.running_plugin is None:
            raise RuntimeError(
                "No running plugin to retrieve configuration for!"
            )

        username = self.username or self.default_username() or "DEFAULT"
        full_key = f"plugin-{self.running_plugin}-{key}"

        return self.config.get(username, full_key, fallback=None)

    # TODO: this is more of an argparsing function than it is a config function
    # might be better to move this to argparsing during refactor and just have
    # configuration return defaults or keys or something
    def update(
        self, namespace: argparse.Namespace, allowed_defaults: List[str]
    ) -> argparse.Namespace:
        # pylint: disable=too-many-branches
        """
        This updates a Namespace (as returned by ArgumentParser) with config values
        if they aren't present in the Namespace already.

        :param namespace: The argparse namespace parsed from the user's input
        :type namespace: argparse.Namespace
        :param allowed_defaults: A list of allowed default keys to pull from the config.
        :type allowed_defaults: List[str]

        :returns: The updated namespace.
        :rtype: argparse.Namespace
        """
        if self.used_env_token and self.config is None:
            return None

        username = self.username or self.default_username()
        if not self.config.has_option(username, "token") and not os.environ.get(
            ENV_TOKEN_NAME, None
        ):
            print(f"User {username} is not configured.", file=sys.stderr)
            sys.exit(ExitCodes.USERNAME_ERROR)
        if (
            not self.config.has_section(username)
            and self.config.default_section is None
        ) or allowed_defaults is None:
            return namespace

        warn_dict = {}
        ns_dict = vars(namespace)
        for key in allowed_defaults:
            if key not in ns_dict:
                continue
            if ns_dict[key] is not None:
                continue
            # plugins set config options that start with 'plugin-'
            # these don't get included in the updated namespace
            if key.startswith("plugin-"):
                continue

            value = self.config.get(username, key, fallback=ns_dict.get(key))

            if not value:
                continue

            if key == "authorized_users":
                ns_dict[key] = [value]
                warn_dict[key] = [value]
            else:
                ns_dict[key] = value
                warn_dict[key] = value

        if not any(
            x in ["--suppress-warnings", "--no-headers"] for x in sys.argv
        ):
            print(
                f"Using default values: {warn_dict}; "
                "use the --no-defaults flag to disable defaults",
                file=sys.stderr,
            )
        return argparse.Namespace(**ns_dict)

    def write_config(self):
        """
        Saves the config file as it is right now.  This can be used by plugins
        to save values they've set, and is used internally to update the config
        on disk when a new user if configured.
        """
        with open(_get_config_path(), "w", encoding="utf-8") as f:
            self.config.write(f)

    def configure(
        self,
    ):  # pylint: disable=too-many-branches,too-many-statements,too-many-locals
        """
        This assumes we're running interactively, and prompts the user
        for a series of defaults in order to make future CLI calls
        easier. This also sets up the config file.
        """
        # If configuration has already been done in this run, don't do it again.
        if self._configured:
            return

        config = {}

        # we're configuring the default user if there is no default user configured
        # yet
        is_default = not self.config.has_option("DEFAULT", "default-user")

        username = None
        token = None

        print(
            "Welcome to the Linode CLI.  This will walk you through some initial setup."
        )

        if ENV_TOKEN_NAME in os.environ:
            print(
                f"Using token from {ENV_TOKEN_NAME}.\n"
                "Note that no token will be saved in your configuration file.\n"
                f"    * If you lose or remove {ENV_TOKEN_NAME}.\n"
                f"    * All profiles will use {ENV_TOKEN_NAME}."
            )
            username = "DEFAULT"
            token = os.getenv(ENV_TOKEN_NAME)

        else:
            if _check_browsers() and not self.configure_with_pat:
                print(
                    "The CLI will use its web-based authentication to log you in.\n"
                    "If you prefer to supply a Personal Access Token,"
                    "use `linode-cli configure --token`."
                )
                input(
                    "Press enter to continue. "
                    "This will open a browser and proceed with authentication."
                )
                username, config["token"] = _get_token_web(self.base_url)
            else:
                username, config["token"] = _get_token_terminal(self.base_url)
            token = config["token"]

        print(f"\nConfiguring {username}\n")

        # Configuring Defaults
        regions = sorted(
            [
                r["id"]
                for r in _do_get_request(self.base_url, "/regions")["data"]
            ]
        )
        types = sorted(
            [
                t["id"]
                for t in _do_get_request(self.base_url, "/linode/types")["data"]
            ]
        )
        images = sorted(
            [i["id"] for i in _do_get_request(self.base_url, "/images")["data"]]
        )

        is_full_access = _check_full_access(self.base_url, token)

        auth_users = []

        if is_full_access:
            users = _do_get_request(
                self.base_url,
                "/account/users",
                token=token,
                # Allow 401 responses so tokens without
                # account perms can be configured
                status_validator=lambda status: status == 401,
            )

            if "data" in users:
                auth_users = sorted(
                    [u["username"] for u in users["data"] if "ssh_keys" in u]
                )

        # get the preferred things
        config["region"] = _default_thing_input(
            "Default Region for operations.",
            regions,
            "Default Region (Optional): ",
            "Please select a valid Region, or press Enter to skip",
            current_value=_config_get_with_default(
                self.config, username, "region"
            ),
        )

        config["type"] = _default_thing_input(
            "Default Type of Linode to deploy.",
            types,
            "Default Type of Linode (Optional): ",
            "Please select a valid Type, or press Enter to skip",
            current_value=_config_get_with_default(
                self.config, username, "type"
            ),
        )

        config["image"] = _default_thing_input(
            "Default Image to deploy to new Linodes.",
            images,
            "Default Image (Optional): ",
            "Please select a valid Image, or press Enter to skip",
            current_value=_config_get_with_default(
                self.config, username, "image"
            ),
        )

        if auth_users:
            config["authorized_users"] = _default_thing_input(
                "Select the user that should be given default SSH access to new Linodes.",
                auth_users,
                "Default Option (Optional): ",
                "Please select a valid Option, or press Enter to skip",
                current_value=_config_get_with_default(
                    self.config, username, "authorized_users"
                ),
            )

        if _bool_input("Configure a custom API target?", default=False):
            self._configure_api_target(config)

        if _bool_input("Suppress API Version Warnings?", default=False):
            config["suppress-version-warning"] = "true"

        # save off the new configuration
        if username != "DEFAULT" and not self.config.has_section(username):
            self.config.add_section(username)

        if not is_default:
            if username != self.default_username():
                is_default = _bool_input(
                    "Make this user the default when using the CLI?"
                )

            if not is_default:  # they didn't change the default user
                print(
                    f"Active user will remain {self.config.get('DEFAULT', 'default-user')}"
                )

        if is_default:
            # if this is the default user, make it so
            self.config.set("DEFAULT", "default-user", username)
            print(f"Active user is now {username}")

        for k, v in config.items():
            if v is None:
                if self.config.has_option(username, k):
                    self.config.remove_option(username, k)

                continue

            self.config.set(username, k, v)

        self.write_config()
        os.chmod(_get_config_path(), 0o600)
        self._configured = True

    @staticmethod
    def _configure_api_target(config: Dict[str, Any]):
        """
        Configure the API target with custom parameters.

        :param config: A dictionary containing the configuration parameters for the API target.
        :type config: Dict[str, Any]
        """
        config["api_host"] = _default_text_input(
            "NOTE: Skipping this field will use the default Linode API host.\n"
            'API host override (e.g. "api.dev.linode.com")',
            optional=True,
        )

        config["api_version"] = _default_text_input(
            "NOTE: Skipping this field will use the default Linode API version.\n"
            'API version override (e.g. "v4beta")',
            optional=True,
        )

        config["api_scheme"] = _default_text_input(
            "NOTE: Skipping this field will use the HTTPS scheme.\n"
            'API scheme override (e.g. "https")',
            optional=True,
        )

    def _handle_no_default_user(self):  # pylint: disable=too-many-branches
        """
        Handles the case where there is no default user in the config.
        """
        users = [c for c in self.config.sections() if c != "DEFAULT"]

        if len(users) == 1:
            # only one user configured - they're the default
            self.config.set("DEFAULT", "default-user", users[0])
            self.write_config()
            return

        if len(users) == 0:
            # config is new or _really_ old
            token = self.config.get("DEFAULT", "token", fallback=None)

            if token is not None:
                # there's a token in the config - configure that user
                u = _do_get_request(
                    self.base_url, "/profile", token=token, exit_on_error=False
                )

                if "errors" in u:
                    # this token was bad - reconfigure
                    self.configure()
                    return

                # setup config for this user
                username = u["username"]

                self.config.set("DEFAULT", "default-user", username)
                self.config.add_section(username)
                self.config.set(username, "token", token)

                config_keys = (
                    "region",
                    "type",
                    "image",
                    "mysql_engine",
                    "postgresql_engine",
                    "authorized_keys",
                    "api_host",
                    "api_version",
                    "api_scheme",
                )

                for key in config_keys:
                    if not self.config.has_option("DEFAULT", key):
                        continue

                    self.config.set(
                        username, key, self.config.get("DEFAULT", key)
                    )

                self.write_config()
            else:
                # got nothin', reconfigure
                self.configure()

            # this should be handled
            return

        # more than one user - prompt for the default
        print("Please choose the active user.  Configured users are:")
        for u in users:
            print(f" {u}")
        print()

        while True:
            username = input("Active user: ")

            if username in users:
                self.config.set("DEFAULT", "default-user", username)
                self.write_config()
                return
            print(f"No user {username}")

    def set_custom_alias(self, alias: str, command: str):
        """
        Sets a custom alias for a Linode CLI command.

        :param alias: The custom alias name.
        :param command: The command the custom alias maps to.
        """
        if not self.config.has_section("custom_aliases"):
            self.config.add_section("custom_aliases")

        self.config.set("custom_aliases", alias, command)
        self.write_config()

    def remove_custom_alias(self, alias: str, command: str):
        """
        Removes a custom alias from the Linode CLI configuration.

        :param alias: The alias name to remove.
        :param command: The command the alias is mapped to.
        """
        if not self.config.has_section("custom_aliases"):
            print("Error: No custom aliases have been set.", file=sys.stderr)
            return

        if not self.config.has_option("custom_aliases", alias):
            print(
                f"Error: Custom alias '{alias}' does not exist.",
                file=sys.stderr,
            )
            return

        # Check if the alias maps to the given command
        existing_command = self.config.get("custom_aliases", alias)
        if existing_command != command:
            print(
                f"Error: Custom alias '{alias}' is mapped to "
                f"'{existing_command}', not '{command}'.",
                file=sys.stderr,
            )
            return

        # Remove the alias and update the config
        self.config.remove_option("custom_aliases", alias)
        self.write_config()

    def get_custom_aliases(self) -> Dict[str, str]:
        """
        Retrieves all stored custom command aliases from the config.

        :return: A dictionary mapping custom alias names to their respective commands.
        """
        return (
            dict(self.config.items("custom_aliases"))
            if (self.config.has_section("custom_aliases"))
            else {}
        )
