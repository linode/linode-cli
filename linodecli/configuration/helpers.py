"""
General helper functions for configuraiton
"""

import configparser
import os
import webbrowser

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

            if self.config.has_option("DEFAULT", "region"):
                self.config.set(
                    username, "region", self.config.get("DEFAULT", "region")
                )

            if self.config.has_option("DEFAULT", "type"):
                self.config.set(
                    username, "type", self.config.get("DEFAULT", "type")
                )

            if self.config.has_option("DEFAULT", "image"):
                self.config.set(
                    username, "image", self.config.get("DEFAULT", "image")
                )

            if self.config.has_option("DEFAULT", "mysql_engine"):
                self.config.set(
                    username,
                    "mysql_engine",
                    self.config.get("DEFAULT", "mysql_engine"),
                )

            if self.config.has_option("DEFAULT", "postgresql_engine"):
                self.config.set(
                    username,
                    "postgresql_engine",
                    self.config.get("DEFAULT", "postgresql_engine"),
                )

            if self.config.has_option("DEFAULT", "authorized_keys"):
                self.config.set(
                    username,
                    "authorized_keys",
                    self.config.get("DEFAULT", "authorized_keys"),
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
