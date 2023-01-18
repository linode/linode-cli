"""
Handles configuring the cli, as well as loading configs so that they can be
used elsewhere.
"""

import os
import sys
import argparse
import webbrowser

from .auth import (
    _get_token_web,
    _check_full_access,
    _do_get_request,
    _get_token_terminal,
)
from .helpers import (
    _default_thing_input,
    _get_config,
    _get_config_path,
    _handle_no_default_user
)

ENV_TOKEN_NAME = "LINODE_CLI_TOKEN"

# this is a list of browser that _should_ work for web-based auth.  This is mostly
# intended to exclude lynx and other terminal browsers which could be opened, but
# won't work.
KNOWN_GOOD_BROWSERS = {
    "chrome",
    "firefox",
    "mozilla",
    "netscape",
    "opera",
    "safari",
    "chromium",
    "chromium-browser",
    "epiphany",
}

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

    def set_user(self, username):
        """
        Sets the acting username.  If this username is not in the config, this is
        an error.  This overrides the default username
        """
        if not self.config.has_section(username):
            print(f"User {username} is not configured!")
            sys.exit(1)

        self.username = username

    def default_username(self):
        """
        Returns the default-user Username
        """
        if self.config.has_option("DEFAULT", "default-user"):
            return self.config.get("DEFAULT", "default-user")
        return ""

    def update_namespace(self, namespace, new_dict):
        """
        In order to update the namespace, we need to turn it into a dict, modify it there,
        then reconstruct it with the exploded dict.
        """
        ns_dict = vars(namespace)
        warn_dict = {}
        for k in new_dict:
            if k.startswith("plugin-"):
                # plugins set config options that start with 'plugin-' - these don't
                # get included in the updated namespace
                continue
            if k in ns_dict and isinstance(k, list):
                ns_dict[k].append(new_dict[k])
            if k in ns_dict and ns_dict[k] is None:
                warn_dict[k] = new_dict[k]
                ns_dict[k] = new_dict[k]
        if not any(x in ["--suppress-warnings", "--no-headers"] for x in sys.argv):
            print(
                f"using default values: {warn_dict}, use --no-defaults flag to disable defaults"
            )
        return argparse.Namespace(**ns_dict)

    def update(self, namespace, allowed_defaults):
        """
        This updates a Namespace (as returned by ArgumentParser) with config values
        if they aren't present in the Namespace already.
        """
        if self.used_env_token and self.config is None:
            # the CLI is using a token defined in the environment; as such, we may
            # not have actually loaded a config file.  That's fine, there are just
            # no defaults
            return None

        username = self.username or self.default_username()

        if not self.config.has_option(username, "token") and not os.environ.get(
            ENV_TOKEN_NAME, None
        ):
            print(f"User {username} is not configured.")
            sys.exit(1)

        if self.config.has_section(username) and allowed_defaults:
            # update_dicts = {
            #     default_key: self.config.get(username, default_key)
            #     for default_key in allowed_defaults
            #     if self.config.has_option(username, default_key)
            #     }
            update_dicts = {}
            for default_key in allowed_defaults:
                if not self.config.has_option(username, default_key):
                    continue
                value = self.config.get(username, default_key)
                if default_key == "authorized_users":
                    update_dicts[default_key] = [value]
                else:
                    update_dicts[default_key] = value

            return self.update_namespace(namespace, update_dicts)
        return namespace

    def get_token(self):
        """
        Returns the token for a configured user
        """
        if self.used_env_token:
            return os.environ.get(ENV_TOKEN_NAME, None)

        if self.config.has_option(self.username or self.default_username(), "token"):
            return self.config.get(self.username or self.default_username(), "token")
        return ""

    def remove_user(self, username):
        """
        Removes the requested user from the config.  If the user is the default,
        this exits with error
        """
        if self.default_username() == username:
            print(
                f"Cannot remote {username} as they are the default user! You can "
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

    # plugin methods - these are intended for plugins to utilize to store their
    # own persistent config information
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
            raise RuntimeError("No running plugin to retrieve configuration for!")

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
            raise RuntimeError("No running plugin to retrieve configuration for!")

        username = self.username or self.default_username()
        full_key = f"plugin-{self.running_plugin}-{key}"

        if not self.config.has_option(username, full_key):
            return None

        return self.config.get(username, full_key)

    def write_config(self, silent=False):
        """
        Saves the config file as it is right now.  This can be used by plugins
        to save values they've set, and is used internally to update the config
        on disk when a new user if configured.

        :param silent: If True, does not print a message noting the config file
                       has been updated.  This is primarily intended for silently
                       updated the config file from one version to another.
        :type silent: bool
        """

        # Create the ~/.config directory if it does not exist
        if not os.path.exists(f"{os.path.expanduser('~')}/.config"):
            os.makedirs(f"{os.path.expanduser('~')}/.config")

        with open(_get_config_path(), "w", encoding="utf-8") as f:
            self.config.write(f)

        if not silent:
            print(f"\nConfig written to {_get_config_path()}")


    def configure(self):  # pylint: disable=too-many-branches,too-many-statements
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
            """Welcome to the Linode CLI.  This will walk you through some initial setup."""
        )

        if ENV_TOKEN_NAME in os.environ:
            print(
                """Using token from {env_token_name}.
Note that no token will be saved in your configuration file.
    * If you lose or remove {env_token_name}.
    * All profiles will use {env_token_name}.""".format(
                    env_token_name=ENV_TOKEN_NAME
                )
            )
            username = "DEFAULT"
            token = os.getenv(ENV_TOKEN_NAME)

        else:
            # let's see if we _can_ use web
            can_use_browser = True
            try:
                webbrowser.get()
            except webbrowser.Error:
                # there are no browsers installed
                can_use_browser = False

            if can_use_browser and not KNOWN_GOOD_BROWSERS.intersection(
                webbrowser._tryorder  # pylint: disable=protected-access
            ):
                print()
                print(
                    "This tool defaults to web-based authentication, however "
                    "no known-working browsers were found."
                )

                while True:
                    r = input("Try it anyway? [y/N]: ")
                    if r.lower() in "yn ":
                        can_use_browser = r.lower() == "y"
                        break

            if self.configure_with_pat or not can_use_browser:
                username, config["token"] = _get_token_terminal(self.base_url)
            else:
                # pylint: disable=line-too-long
                print()
                print(
                    "The CLI will use its web-based authentication to log you in.  "
                    "If you prefer to supply a Personal Access Token, use `linode-cli configure --token`. "
                )
                print()
                input(
                    "Press enter to continue.  This will open a browser and proceed with authentication."
                )
                username, config["token"] = _get_token_web(self.base_url)
                # pylint: enable=line-too-long

            token = config["token"]

        print()
        print(f"Configuring {username}")
        print()

        regions = [r["id"] for r in _do_get_request(self.base_url, "/regions")["data"]]
        types = [t["id"] for t in _do_get_request(self.base_url, "/linode/types")["data"]]
        images = [i["id"] for i in _do_get_request(self.base_url, "/images")["data"]]

        is_full_access = _check_full_access(self.base_url, token)

        auth_users = []

        if is_full_access:
            auth_users = [
                u["username"]
                for u in _do_get_request(
                    self.base_url, "/account/users", exit_on_error=False, token=token
                )["data"]
                if "ssh_keys" in u
            ]

        # get the preferred things
        config["region"] = _default_thing_input(
            "Default Region for operations.",
            regions,
            "Default Region (Optional): ",
            "Please select a valid Region, or press Enter to skip",
        )

        config["type"] = _default_thing_input(
            "Default Type of Linode to deploy.",
            types,
            "Default Type of Linode (Optional): ",
            "Please select a valid Type, or press Enter to skip",
        )

        config["image"] = _default_thing_input(
            "Default Image to deploy to new Linodes.",
            images,
            "Default Image (Optional): ",
            "Please select a valid Image, or press Enter to skip",
        )

        if auth_users:
            config["authorized_users"] = _default_thing_input(
                "Select the user that should be given default SSH access to new Linodes.",
                auth_users,
                "Default Option (Optional): ",
                "Please select a valid Option, or press Enter to skip",
            )

        # save off the new configuration
        if username != "DEFAULT" and not self.config.has_section(username):
            self.config.add_section(username)

        if not is_default:
            if username != self.default_username():
                while True:
                    value = input(
                        "Make this user the default when using the CLI? [y/N]: "
                    )

                    if value.lower() in "yn":
                        is_default = value.lower() == "y"
                        break
                    if not value.strip():
                        break

            if not is_default:  # they didn't change the default user
                print(
                    f"Active user will remain {self.config.get('DEFAULT', 'default-user')}"
                )

        if is_default:
            # if this is the default user, make it so
            self.config.set("DEFAULT", "default-user", username)
            print(f"Active user is now {username}")

        for k, v in config.items():
            if v:
                self.config.set(username, k, v)

        self.write_config()
        os.chmod(_get_config_path(), 0o600)
        self._configured = True
