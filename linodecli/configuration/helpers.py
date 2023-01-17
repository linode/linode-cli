"""
General helper functions for configuraiton
"""

import os
import sys

import requests

try:
    # python3
    import configparser
except ImportError:
    # python2
    import ConfigParser as configparser

LEGACY_CONFIG_DIR = os.path.expanduser("~")
LEGACY_CONFIG_NAME = ".linode-cli"

CONFIG_DIR = os.environ.get("XDG_CONFIG_HOME", f"{os.path.expanduser('~')}/.config")
CONFIG_NAME = "linode-cli"

TOKEN_GENERATION_URL = "https://cloud.linode.com/profile/tokens"

def _do_request(method, url, token=None, exit_on_error=None, body=None):  # pylint: disable=too-many-arguments
    """
    Does helper requests during configuration
    """
    headers = {}

    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
        headers["Content-type"] = "application/json"

    result = method(self.base_url + url, headers=headers, json=body)

    _handle_response_status(result, exit_on_error=exit_on_error)

    return result.json()

def _username_for_token(token):
    """
    A helper function that returns the username assocaited with a token by
    requesting it from the API
    """
    u = _do_get_request("/profile", token=token, exit_on_error=False)
    if "errors" in u:
        reasons = ",".join([c["reason"] for c in u["errors"]])
        print(f"That token didn't work: {reasons}")
        return None

    return u["username"]

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

def _get_config_path():
    """
    Returns the path to the config file.
    """
    path = f"{LEGACY_CONFIG_DIR}/{LEGACY_CONFIG_NAME}"
    if os.path.exists(path):
        return path

    return f"{CONFIG_DIR}/{CONFIG_NAME}"

def _get_token_terminal():
    """
    Handles prompting the user for a Personal Access Token and checking it
    to ensure it works.
    """
    print(
        f"""
First, we need a Personal Access Token.  To get one, please visit
{TOKEN_GENERATION_URL} and click
"Create a Personal Access Token".  The CLI needs access to everything
on your account to work correctly."""
    )

    while True:
        token = input("Personal Access Token: ")

        username = _username_for_token(token)
        if username is not None:
            break

    return username, token

def _default_thing_input(
    ask, things, prompt, error, optional=True
):  # pylint: disable=too-many-arguments
    """
    Requests the user choose from a list of things with the given prompt and
    error if they choose something invalid.  If optional, the user may hit
    enter to not configure this option.
    """
    print(f"\n{ask}  Choices are:")
    for ind, thing in enumerate(things):
        print(f" {ind + 1} - {thing}")
    print()

    ret = ""
    while True:
        choice = input(prompt)

        if choice:
            try:
                choice = int(choice)
                choice = things[choice - 1]
            except:
                pass

            if choice in list(things):
                ret = choice
                break
            print(error)
        else:
            if optional:
                break
            print(error)
    return ret

def _do_get_request(url, token=None, exit_on_error=True):
    """
    Does helper get requests during configuration
    """
    return _do_request(
        method=requests.get, url=url, token=token, exit_on_error=exit_on_error
    )

@staticmethod
def _handle_response_status(response, exit_on_error=None):
    if 199 < response.status_code < 300:
        return

    print(f"Could not contact {response.url} - Error: {response.status_code}")
    if exit_on_error:
        sys.exit(4)

def _check_full_access(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    result = requests.get(
        base_url + "/profile/grants", headers=headers, timeout=120
    )

    _handle_response_status(result, exit_on_error=True)

    return result.status_code == 204

def _handle_no_default_user():
    """
    Handle the case that there is no default user in the config
    """
    users = [c for c in self.config.sections() if c != "DEFAULT"]

    if len(users) == 1:
        # only one user configured - they're the default
        self.config.set("DEFAULT", "default-user", users[0])
        self.write_config(silent=True)
        return

    if len(users) == 0:
        # config is new or _really_ old
        token = self.config.get("DEFAULT", "token")

        if token is not None:
            # there's a token in the config - configure that user
            u = _do_get_request("/profile", token=token, exit_on_error=False)

            if "errors" in u:
                # this token was bad - reconfigure
                self.configure()
                return

            # setup config for this user
            username = u["username"]

            self.config.set("DEFAULT", "default-user", username)
            self.config.add_section(username)
            self.config.set(username, "token", token)
            self.config.set(
                username, "region", self.config.get("DEFAULT", "region")
            )
            self.config.set(username, "type", self.config.get("DEFAULT", "type"))
            self.config.set(username, "image", self.config.get("DEFAULT", "image"))
            self.config.set(
                username,
                "authorized_keys",
                self.config.get("DEFAULT", "authorized_keys"),
            )

            self.write_config(silent=True)
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
