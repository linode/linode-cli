"""
The ssh plugin allows sshing into Linodes by label or ID

Invoke as follows::

   linode-cli ssh [USERNAME@]LINODE_LABEL [SSH ARGS..]

   LINODE_LABEL - the label of the Linode to ssh into
   USERNAME - the user to ssh into the Linode as.  Defaults to the current user
"""

import argparse
import subprocess
import sys
from sys import platform
from typing import Any, Dict, Optional, Tuple

from linodecli.exit_codes import ExitCodes
from linodecli.plugins import inherit_plugin_args


def call(args, context):  # pylint: disable=too-many-branches
    """
    Invokes this plugin
    """
    if platform == "win32":
        print(
            "This plugin is not currently supported in Windows.  For more "
            "information or to suggest a fix, please visit "
            "https://github.com/linode/linode-cli",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.REQUEST_FAILED)

    parser = inherit_plugin_args(
        argparse.ArgumentParser("linode-cli ssh", add_help=True)
    )

    parser.add_argument(
        "label",
        metavar="[USERNAME@]LABEL",
        nargs="?",
        type=str,
        help="The label of the Linode to SSH into, optionally with "
        "a username before it in USERNAME@LABEL format.  If no "
        "username is given, defaults to the current user.",
    )
    parser.add_argument(
        "-6",
        action="store_true",
        help="If given, uses the Linode's SLAAC address for SSH.",
    )
    parser.add_argument(
        "-d",
        action="store_true",
        help="If given, uses the Lindoe's domain name for SSH",
    )

    parsed, args = parser.parse_known_args(args)

    if not parsed.label:
        parser.print_help()
        sys.exit(ExitCodes.SUCCESS)

    username, label = parse_target_components(parsed.label)

    target = find_linode_with_label(context, label)

    if target["status"] != "running":
        print(
            f"{label} is not running (status is {target['status']}); operation aborted.",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.REQUEST_FAILED)

    # find a public IP Address to use
    address = parse_target_address(parsed, target)
    if username:
        address = username + "@" + address

    # do it
    code = 0
    try:
        # tack the remaining unparsed args onto the end - those are args for ssh
        subprocess.check_call(["ssh", address] + args)
    except subprocess.CalledProcessError as e:
        # ssh exited with non-zero status code
        code = e.returncode

    # exit with the same code as ssh
    sys.exit(code)


def find_linode_with_label(context, label: str) -> str:
    """
    Finds a Linode Instance with the given label.
    If no matching instance is found, the plugin prints similar instances
    and exits.
    """
    result, potential_matches = context.client.call_operation(
        "linodes", "list", filters={"label": {"+contains": label}}
    )

    if result != 200:
        print(f"Could not retrieve Linode: {result} error", file=sys.stderr)
        sys.exit(ExitCodes.REQUEST_FAILED)

    potential_matches = potential_matches["data"]

    # see if we got a match
    for match in potential_matches:
        if match["label"] == label:
            return match

    # no match - stop
    print(f"No Linode found for label {label}")

    if potential_matches:
        print("Did you mean: ")
        print("\n".join([f" {p['label']}" for p in potential_matches]))

    sys.exit(ExitCodes.REQUEST_FAILED)


def parse_target_components(label: str) -> Tuple[Optional[str], str]:
    """
    Returns the components (username, label) of the
    given `label` argument.
    """

    if "@" in label:
        username, label = label.split("@", 1)
        return username, label

    return None, label


def parse_target_address(
    parsed: argparse.Namespace, target: Dict[str, Any]
) -> str:
    """
    Returns the first available public IP address
    given the conditions defined in parsed.
    """
    if getattr(
        parsed, "6"
    ):  # this is necessary since the name isn't a valid python variable name
        return target["ipv6"].split("/")[0]

    for ip in target["ipv4"]:
        # Ignore private IPs
        if ip.startswith("192.168"):
            continue

        if getattr(parsed, "d"):
            ip = ip.replace(".", "-") + ".ip.linodeusercontent.com"

        return ip
