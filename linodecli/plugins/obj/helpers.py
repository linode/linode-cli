"""
The helper functions for the object storage plugin.
"""
import getpass
import os
import socket
import sys
import time
from argparse import ArgumentTypeError
from datetime import datetime

from terminaltables import SingleTable

from linodecli.cli import CLI
from linodecli.configuration import _do_get_request
from linodecli.configuration.helpers import _default_thing_input
from linodecli.plugins.obj.config import (
    DATE_FORMAT,
    ENV_ACCESS_KEY_NAME,
    ENV_SECRET_KEY_NAME,
    NO_ACCESS_ERROR,
    NO_SCOPES_ERROR,
)


class ProgressPercentage:  # pylint: disable=too-few-public-methods
    """
    Progress bar class for boto3 file upload/download
    """

    def __init__(self, file_size: int, bar_width: int):
        self.size = file_size
        self.uploaded = 0
        self.bar_width = bar_width

    def __call__(self, bytes_amount: int):
        if bytes_amount == 0:
            return
        if not self.size:
            return
        self.uploaded += bytes_amount
        percentage = self.bar_width * (self.uploaded / self.size)
        progress = int(percentage)
        progress_bar = ("#" * progress) + ("-" * (self.bar_width - progress))
        print(f"\r |{progress_bar}| {percentage:.1f}%", end="\r")
        if self.uploaded == self.size:
            print()


def _progress(cur: float, total: float):
    """
    Draws the upload progress bar.
    """
    # We can't divide by zero :)
    if total == 0.0:
        return

    percent = f"{100 * (cur / float(total)):.1f}"
    progress = int(100 * cur // total)
    progress_bar = ("#" * progress) + ("-" * (100 - progress))
    print(f"\r |{progress_bar}| {percent}%", end="\r")

    if cur == total:
        print()


def restricted_int_arg_type(
    max: int, min: int = 1
):  # pylint: disable=redefined-builtin
    """
    An ArgumentParser arg type for integers that restricts the value to between `min` and `max`
    (inclusive for both.)
    """

    def restricted_int(string: str):
        err_msg = f"Value must be an integer between {min} and {max}"
        try:
            value = int(string)
        except ValueError as e:
            # argparse can handle ValueErrors, but shows an unfriendly "invalid restricted_int
            # value: '0.1'" message, so catch and raise with a better message.
            raise ArgumentTypeError(err_msg) from e
        if value < min or value > max:
            raise ArgumentTypeError(err_msg)
        return value

    return restricted_int


def _convert_datetime(dt: datetime):
    """
    Given a string in INCOMING_DATE_FORMAT, returns a string in DATE_FORMAT
    """

    return dt.strftime(DATE_FORMAT)


def _pad_to(
    val, length=10, right_align=False
):  # pylint: disable=unused-argument
    """
    Pads val to be at minimum length characters long
    """
    ret = str(val)
    padding = ""

    if len(ret) < 10:
        padding = " " * (10 - len(ret))

    if right_align:
        ret = padding + ret
    else:
        ret = ret + padding

    return ret


def _denominate(total):
    """
    Coverts bucket size to human readable bytes.
    """
    total = float(total)
    denomination = ["KB", "MB", "GB", "TB"]
    for x in denomination:
        if total > 1024:
            total = total / 1024
        if total < 1024:
            total = round(total, 2)
            total = str(total) + " " + x
            break
    return total


# helper functions for output
def _borderless_table(data):
    """
    Returns a terminaltables.SingleTable object with no borders and correct padding
    """
    tab = SingleTable(data)
    tab.inner_heading_row_border = False
    tab.inner_column_border = False
    tab.outer_border = False
    tab.padding_left = 0
    tab.padding_right = 2

    return tab


def _get_s3_creds(client: CLI, force: bool = False):
    """
    Retrieves stored s3 creds for the acting user from the config, or generates new
    creds using the client and stores them if none exist

    :param client: The client object from the invoking PluginContext
    :type client: linodecli.CLI
    :param force: If True, get new creds even if there are already creds stored.
                  This is used to rotate creds.
    :type force: bool

    :returns: The access key and secret key for this user
    :rtype: tuple(str, str)
    """
    access_key = client.config.plugin_get_value("access-key")
    secret_key = client.config.plugin_get_value("secret-key")

    if force or access_key is None:
        # this means there are no stored s3 creds for this user - set them up

        # but first - is there actually a config?  If we got this far, creds aren't
        # being provided by the environment, but if the CLI is running without a
        # config, we shouldn't generate new keys (or we'd end up doing so with each
        # request) - instead ask for them to be set up.
        if client.config.get_value("token") is None:
            print(
                "You are running the Linode CLI without a configuration file, but "
                "object storage keys were not configured.  "
                "Please set the following variables in your environment: "
                f"'{ENV_ACCESS_KEY_NAME}' and '{ENV_SECRET_KEY_NAME}'.  If you'd rather "
                "configure the CLI, unset the 'LINODE_CLI_TOKEN' environment "
                "variable and then run `linode-cli configure`."
            )
            sys.exit(1)

        # before we do anything, can they do object storage?
        status, resp = client.call_operation("account", "view")

        if status != 200:
            if status == 401:
                # special case - oauth token isn't allowed to do this
                print(NO_SCOPES_ERROR)
                sys.exit(4)
            if status == 403:
                # special case - restricted users can't use obj
                print(NO_ACCESS_ERROR)
                sys.exit(4)
            # something went wrong - give up
            print("Key generation failed!")
            sys.exit(4)

        # label caps at 50 characters - trim some stuff maybe
        # static characters in label account for 13 total
        # timestamp is 10 more
        # allow 13 characters both for username and hostname
        timestamp_part = str(time.time()).split(".", maxsplit=1)[0]
        truncated_user = getpass.getuser()[:13]
        truncated_hostname = socket.gethostname()[:13]

        creds_label = (
            f"linode-cli-{truncated_user}@{truncated_hostname}-{timestamp_part}"
        )

        if len(creds_label) > 50:
            # if this is somehow still too long, trim from the front
            creds_label = creds_label[50 - len(creds_label) :]

        status, resp = client.call_operation(
            "object-storage", "keys-create", ["--label", f"{creds_label}"]
        )

        if status != 200:
            if status == 401:
                # special case - oauth token isn't allowed to do this
                print(NO_SCOPES_ERROR)
                sys.exit(4)
            if status == 403:
                # special case - restricted users can't use obj
                print(NO_ACCESS_ERROR)
                sys.exit(4)
            # something went wrong - give up
            print("Key generation failed!")
            sys.exit(3)

        access_key = resp["access_key"]
        secret_key = resp["secret_key"]

        client.config.plugin_set_value("access-key", access_key)
        client.config.plugin_set_value("secret-key", secret_key)
        client.config.write_config()

    return access_key, secret_key


def regenerate_s3_credentials(cli: CLI):
    """
    Force regenerate object storage access key and secret key.
    """
    print("Regenerating Object Storage keys..")
    _get_s3_creds(cli, force=True)
    print("Done.")
    print(
        "Warning: Your old Object Storage keys _were not_ automatically expired!  If you want "
        "to expire them, see `linode-cli object-storage keys-list` and "
        "`linode-cli object-storage keys-delete [KEYID]`."
    )


def _configure_plugin(client: CLI):
    """
    Configures a default cluster value.
    """
    clusters = [
        c["id"]
        for c in _do_get_request(  # pylint: disable=protected-access
            client.config.base_url,
            "/object-storage/clusters",
            token=client.config.get_value("token"),
        )["data"]
    ]

    cluster = _default_thing_input(  # pylint: disable=protected-access
        "Configure a default Cluster for operations.",
        clusters,
        "Default Cluster: ",
        "Please select a valid Cluster",
        optional=False,  # this is the only configuration right now
    )

    client.config.plugin_set_value("cluster", cluster)
    client.config.write_config()


def get_credentials(cli: CLI):
    """
    Get access_key and secret_key of the object storage.
    """
    access_key, secret_key = (
        os.getenv(ENV_ACCESS_KEY_NAME, None),
        os.getenv(ENV_SECRET_KEY_NAME, None),
    )
    if bool(access_key) != bool(secret_key):
        print(
            f"You must set both {ENV_ACCESS_KEY_NAME} "
            f"and {ENV_SECRET_KEY_NAME}, or neither"
        )
        sys.exit(1)

    # not given on command line, so look them up
    if not access_key:
        access_key, secret_key = _get_s3_creds(cli)

    return access_key, secret_key
