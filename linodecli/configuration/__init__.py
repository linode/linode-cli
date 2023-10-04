"""
Handles configuring the cli, as well as loading configs so that they can be
used elsewhere.
"""

import argparse
import os
import sys
from typing import Dict

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
    _handle_no_default_user,
)

ENV_TOKEN_NAME = "LINODE_CLI_TOKEN"


class CLIConfig:
    """
    Generates the necessary config for the Linode CLI
    """

    def __init__(self, base_url, username=None, skip_config=False):
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
            _handle_no_default_user(self)

        environ_token = os.getenv(ENV_TOKEN_NAME, None)

        if (
            not self.config.has_option("DEFAULT", "default-user")
            and not skip_config
            and environ_token is None
        ):
            self.configure()
        elif environ_token is not None:
            self.used_env_token = True

    def default_username(self):
        """
        Returns the default-user Username
        """
        if self.config.has_option("DEFAULT", "default-user"):
            return self.config.get("DEFAULT", "default-user")
        return ""

    def set_user(self, username):
        """
        Sets the acting username.  If this username is not in the config, this is
        an error.  This overrides the default username
        """
        if not self.config.has_section(username):
            print(f"User {username} is not configured!")
            sys.exit(1)

        self.username = username

    def remove_user(self, username):
        """
        Removes the requested user from the config.  If the user is the default,
        this exits with error
        """
        if self.default_username() == username:
            print(
                f"Cannot remove {username} as they are the default user! You can "
                "change the default user with: `linode-cli set-user USERNAME`"
            )
            sys.exit(1)

        if self.config.has_section(username):
            self.config.remove_section(username)
            self.write_config()

    def print_users(self):
        """
        Prints all users available and exits
        """
        print("Configured Users: ")
        default_user = self.default_username()

        for sec in self.config.sections():
            if sec != "DEFAULT":
                print(f'{"*" if sec == default_user else " "}  {sec}')

        sys.exit(0)

    def set_default_user(self, username):
        """
        Sets the default user.  If that user isn't in the config, exits with error
        """
        if not self.config.has_section(username):
            print(f"User {username} is not configured!")
            sys.exit(1)

        self.config.set("DEFAULT", "default-user", username)
        self.write_config()

    def get_token(self):
        """
        Returns the token for a configured user
        """
        if self.used_env_token:
            return os.environ.get(ENV_TOKEN_NAME, None)

        if self.config.has_option(
            self.username or self.default_username(), "token"
        ):
            return self.config.get(
                self.username or self.default_username(), "token"
            )
        return ""

    def get_value(self, key):
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
        username = self.username or self.default_username()

        if not self.config.has_option(username, key):
            return None

        return self.config.get(username, key)

    # plugin methods - these are intended for plugins to utilize to store their
    # own persistent config information
    def plugin_set_value(self, key, value):
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

    def plugin_get_value(self, key):
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

        username = self.username or self.default_username()
        full_key = f"plugin-{self.running_plugin}-{key}"

        if not self.config.has_option(username, full_key):
            return None

        return self.config.get(username, full_key)

    # TODO: this is more of an argparsing function than it is a config function
    # might be better to move this to argparsing during refactor and just have
    # configuration return defaults or keys or something
    def update(
        self, namespace, allowed_defaults
    ):  # pylint: disable=too-many-branches
        """
        This updates a Namespace (as returned by ArgumentParser) with config values
        if they aren't present in the Namespace already.
        """
        if self.used_env_token and self.config is None:
            return None
        username = self.username or self.default_username()
        if not self.config.has_option(username, "token") and not os.environ.get(
            ENV_TOKEN_NAME, None
        ):
            print(f"User {username} is not configured.")
            sys.exit(1)
        if not self.config.has_section(username) or allowed_defaults is None:
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
            value = None
            if self.config.has_option(username, key):
                value = self.config.get(username, key)
            else:
                value = ns_dict[key]

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
                f"using default values: {warn_dict}, "
                "use --no-defaults flag to disable defaults"
            )
        return argparse.Namespace(**ns_dict)

    def write_config(self):
        """
        Saves the config file as it is right now.  This can be used by plugins
        to save values they've set, and is used internally to update the config
        on disk when a new user if configured.
        """
        if not os.path.exists(f"{os.path.expanduser('~')}/.config"):
            os.makedirs(f"{os.path.expanduser('~')}/.config")
        with open(_get_config_path(), "w", encoding="utf-8") as f:
            self.config.write(f)

    def configure(
        self,
    ):  # pylint: disable=too-many-branches,too-many-statements,too-many-locals
        """
        This assumes we're running interactively, and prompts the user
        for a series of defaults in order to make future CLI calls
        easier.  This also sets up the config file.
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
                f"""Using token from {ENV_TOKEN_NAME}.
Note that no token will be saved in your configuration file.
    * If you lose or remove {ENV_TOKEN_NAME}.
    * All profiles will use {ENV_TOKEN_NAME}."""
            )
            username = "DEFAULT"
            token = os.getenv(ENV_TOKEN_NAME)

        else:
            if _check_browsers() and not self.configure_with_pat:
                print(
                    """
The CLI will use its web-based authentication to log you in.
If you prefer to supply a Personal Access Token, use `linode-cli configure --token`.
                    """
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

        regions = [
            r["id"] for r in _do_get_request(self.base_url, "/regions")["data"]
        ]
        types = [
            t["id"]
            for t in _do_get_request(self.base_url, "/linode/types")["data"]
        ]
        images = [
            i["id"] for i in _do_get_request(self.base_url, "/images")["data"]
        ]

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
                auth_users = [
                    u["username"] for u in users["data"] if "ssh_keys" in u
                ]

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
    def _configure_api_target(config: Dict[str, str]):
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
