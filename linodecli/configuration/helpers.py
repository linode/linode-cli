"""
General helper functions for configuraiton
"""

import configparser
import os
import webbrowser
from typing import Any, Callable, Optional

from .auth import _do_get_request

LEGACY_CONFIG_NAME = ".linode-cli"
LEGACY_CONFIG_DIR = os.path.expanduser("~")

CONFIG_NAME = "linode-cli"
CONFIG_DIR = os.environ.get(
    "XDG_CONFIG_HOME", f"{os.path.expanduser('~')}/.config"
)

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


def _get_config_path():
    """
    Returns the path to the config file.
    """
    path = f"{LEGACY_CONFIG_DIR}/{LEGACY_CONFIG_NAME}"
    if os.path.exists(path):
        return path

    return f"{CONFIG_DIR}/{CONFIG_NAME}"


def _get_config(load=True):
    """
    Returns a new ConfigParser object that represents the CLI's configuration.
    If load is false, we won't load the config from disk.

    :param load: If True, load the config from the default path.  Otherwise,
                    don't (and just return an empty ConfigParser)
    :type load: bool
    """
    conf = configparser.ConfigParser()

    if load:
        conf.read(_get_config_path())

    return conf


def _check_browsers():
    # let's see if we _can_ use web
    try:
        webbrowser.get()
    except webbrowser.Error:
        # there are no browsers installed
        return False

    # pylint: disable-next=protected-access
    if not KNOWN_GOOD_BROWSERS.intersection(webbrowser._tryorder):
        print(
            """
This tool defaults to web-based authentication,
however no known-working browsers were found."""
        )
        while True:
            r = input("Try it anyway? [y/N]: ")
            if r.lower() in "yn ":
                return r.lower() == "y"
    return True


def _default_thing_input(
    ask, things, prompt, error, optional=True, current_value=None
):  # pylint: disable=too-many-arguments
    """
    Requests the user choose from a list of things with the given prompt and
    error if they choose something invalid.  If optional, the user may hit
    enter to not configure this option.
    """
    print(f"\n{ask}  Choices are:")

    exists = current_value is not None

    idx_offset = int(exists) + 1

    # If there is a current value, users should have the option to clear it
    if exists:
        print(" 1 - No Default")

    for ind, thing in enumerate(things):
        print(f" {ind + idx_offset} - {thing}")
    print()

    while True:
        choice_idx = input(prompt)

        if not choice_idx:
            # The user wants to skip this config option
            if optional:
                return current_value

            print(error)
            continue

        try:
            choice_idx = int(choice_idx)
        except:
            # Re-prompt if invalid value
            continue

        # The user wants to drop this default
        if exists and choice_idx == 1:
            return None

        # We need to shift the index to account for the "No Default" option
        choice_idx -= idx_offset

        # Validate index
        if choice_idx >= len(things) or choice_idx < 0:
            print(error)
            continue

        # Choice was valid; return
        return things[choice_idx]


def _default_text_input(
    ask: str,
    default: str = None,
    optional: bool = False,
    validator: Callable[[str], Optional[str]] = None,
) -> Optional[str]:  # pylint: disable=too-many-arguments
    """
    Requests the user to enter a certain string of text with the given prompt.
    If optional, the user may hit enter to not configure this option.
    """

    prompt_text = f"\n{ask} "

    if default is not None:
        prompt_text += f"(Default {default})"
    elif optional:
        prompt_text += "(Optional)"

    while True:
        user_input = input(prompt_text + ": ")

        # If the user skips on an optional value, return None
        if user_input == "":
            if default is not None:
                return default

            if optional:
                return None

            print("Please enter a valid value.")
            continue

        # Validate the user's input using the
        # passed in validator.
        if validator is not None:
            validation_result = validator(user_input)

            if validation_result is not None:
                print(validation_result)
                continue

        return user_input


def _bool_input(
    prompt: str, default: bool = True
):  # pylint: disable=too-many-arguments
    """
    Requests the user to enter either `y` or `n` given a prompt.
    """
    while True:
        user_input = input(f"\n{prompt} [y/N]: ").strip().lower()

        if user_input == "":
            return default

        if user_input not in ("y", "n"):
            print("Invalid input. Please input either y or n.")
            continue

        return user_input == "y"


def _config_get_with_default(
    config: configparser.ConfigParser,
    user: str,
    field: str,
    default: Any = None,
) -> Optional[Any]:
    """
    Gets a ConfigParser value and returns a default value if the key isn't found.
    """
    return (
        config.get(user, field) if config.has_option(user, field) else default
    )


def _handle_no_default_user(self):  # pylint: disable=too-many-branches
    """
    Handle the case that there is no default user in the config
    """
    users = [c for c in self.config.sections() if c != "DEFAULT"]

    if len(users) == 1:
        # only one user configured - they're the default
        self.config.set("DEFAULT", "default-user", users[0])
        self.write_config()
        return

    if len(users) == 0:
        # config is new or _really_ old
        token = self.config.get("DEFAULT", "token")

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

                self.config.set(username, key, self.config.get("DEFAULT", key))

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
