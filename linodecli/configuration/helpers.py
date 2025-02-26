"""
General helper functions for configuraiton
"""

import configparser
import math
import os
import webbrowser
from functools import partial
from typing import Any, Callable, List, Optional

LEGACY_CONFIG_NAME = ".linode-cli"
LEGACY_CONFIG_DIR = os.path.expanduser("~")

CONFIG_NAME = "linode-cli"
CONFIG_DIR = os.environ.get(
    "XDG_CONFIG_HOME", f"{os.path.expanduser('~')}/.config"
)

ENV_CONFIG_FILE_PATH = "LINODE_CLI_CONFIG"

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


def _get_config_path() -> str:
    """
    Returns the path to the config file.

    :returns: The path to the local config file.
    :rtype: str
    """
    custom_path = os.getenv(ENV_CONFIG_FILE_PATH, None)

    if custom_path is not None:
        custom_path = os.path.expanduser(custom_path)
        if not os.path.exists(custom_path):
            os.makedirs(os.path.dirname(custom_path), exist_ok=True)
        return custom_path

    path = f"{LEGACY_CONFIG_DIR}/{LEGACY_CONFIG_NAME}"
    if os.path.exists(path):
        return path

    path = f"{CONFIG_DIR}/{CONFIG_NAME}"
    if not os.path.exists(path):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    return path


def _get_config(load: bool = True):
    """
    Returns a new ConfigParser object that represents the CLI's configuration.
    If load is false, we won't load the config from disk.

    :param load: If True, load the config from the default path.  Otherwise,
                    don't (and just return an empty ConfigParser)
    :type load: bool

    :returns: The loaded config parser.
    :rtype: configparser.ConfigParser
    """
    conf = configparser.ConfigParser()

    if load:
        conf.read(_get_config_path())

    return conf


def _check_browsers() -> bool:
    """
    Checks if any browsers on the local machine are installed and usable.

    :returns: Whether at least one known-working browser is found.
    :rtype: bool
    """
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
    ask: str,
    things: List[Any],
    prompt: str,
    error: str,
    optional: bool = True,
    current_value: Optional[Any] = None,
):  # pylint: disable=too-many-arguments
    """
    Requests the user choose from a list of things with the given prompt and
    error if they choose something invalid. If optional, the user may hit
    enter to not configure this option.

    :param ask: The initial question to ask the user.
    :type ask: str
    :param things: A list of options for the user to choose from.
    :type things: List[Any]
    :param prompt: The prompt to show before the user input.
    :type prompt: str
    :param error: The error to display if a user's input is invalid.
    :type error: str
    :param optional: Whether this prompt is optional. Defaults to True.
    :type optional: bool
    :param current_value: The current value of the corresponding field,
                          allowing users to leave a config value unchanged.
    :type current_value: str

    :returns: The user's selected option.
    :rtype: Any
    """
    print(f"\n{ask}  Choices are:")

    exists = current_value is not None

    idx_offset = int(exists) + 1
    pad = partial(_pad_index, total=len(things) + idx_offset)

    # If there is a current value, users should have the option to clear it
    if exists:
        print(f"{pad(1)} - No Default")

    for ind, thing in enumerate(things):
        print(f"{pad(ind + idx_offset)} - {thing}")
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


def _pad_index(idx: int, total: int) -> str:
    # NOTE: The implementation of this function could be less opaque if we're
    # willing to say, "There will never be a case where total > X, because no
    # one could examine and choose from that many options."
    max_padding = math.floor(math.log10(total)) + 1
    num_spaces = max_padding - math.floor(math.log10(idx))

    return " " * num_spaces + str(idx)


def _default_text_input(
    ask: str,
    default: Optional[str] = None,
    optional: bool = False,
    validator: Callable[[str], Optional[str]] = None,
) -> Optional[str]:  # pylint: disable=too-many-arguments
    """
    Requests the user to enter a certain string of text with the given prompt.
    If optional, the user may hit enter to not configure this option.

    :param ask: The initial question to ask the user.
    :type ask: str
    :param default: The default value for this input.
    :type default: Optional[str]
    :param optional: Whether this prompt is optional.
    :type optional: bool
    :param validator: A function to validate the user's input with.
    :type validator: Callable[[str], Optional[str]]

    :returns: The user's input.
    :rtype: str
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
) -> bool:  # pylint: disable=too-many-arguments
    """
    Requests the user to enter either `y` or `n` given a prompt.

    :param prompt: The prompt to ask the user.
    :type prompt: str
    :param default: The default value for this input. Defaults to True.
    :type default: bool

    :returns: The user's input.
    :rtype: bool
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
) -> Any:
    """
    Gets a ConfigParser value and returns a default value if the key isn't found.

    :param user: The user to get a value for.
    :type user: str
    :param field: The name of the field to get the value for.
    :type field: str
    :param default: The default value to use if a value isn't found. Defaults to None.
    :type default: Any

    :returns: The value pulled from the config or the default value.
    :rtype: Any
    """
    return config.get(user, field, fallback=default)
