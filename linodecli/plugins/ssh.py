"""
The ssh plugin allows sshing into Linodes by label or ID

Invoke as follows::

   linode-cli ssh [USERNAME@]LINODE_LABEL [SSH ARGS..]

   LINODE_LABEL - the label of the Linode to ssh into
   USERNAME - the user to ssh into the Linode as.  Defaults to the current user
"""
import argparse
import subprocess
from sys import exit, platform, version_info



def call(args, context):
    """
    Invokes this plugin
    """
    if platform == "win32":
        print(
            "This plugin is not currently supported in Windows.  For more "
            "information or to suggest a fix, please visit "
            "https://github.com/linode/linode-cli"
        )
        exit(1)

    parser = argparse.ArgumentParser("linode-cli ssh", add_help=True)
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

    parsed, args = parser.parse_known_args(args)

    if not parsed.label:
        parser.print_help()
        exit(0)

    label = parsed.label
    username = None
    if "@" in parsed.label:
        username, label = parsed.label.split("@", 1)

    result, potential_matches = context.client.call_operation(
        "linodes", "list", filters={"label": {"+contains": label}}
    )

    if result != 200:
        print("Could not retrieve Linode: {} error".format(result))
        exit(2)

    potential_matches = potential_matches["data"]
    exact_match = None

    # see if we got a match
    for match in potential_matches:
        if match["label"] == label:
            exact_match = match
            break

    if exact_match is None:
        # no match - stop
        print("No Linode found for label {}".format(label))

        if potential_matches:
            print("Did you mean: ")
            print("\n".join([" {}".format(p["label"]) for p in potential_matches]))
        exit(1)

    if exact_match["status"] != "running":
        print(
            "{} is not running (status is {}); operation aborted.".format(
                label, exact_match["status"]
            )
        )
        exit(2)

    # find a public IP Address to use
    public_ip = None

    if getattr(
        parsed, "6"
    ):  # this is necessary since the name isn't a valid python variable name
        public_ip = exact_match["ipv6"].split("/")[0]
    else:
        for ip in exact_match["ipv4"]:
            if not ip.startswith("192.168"):
                public_ip = ip  # TODO - this uses the "first" IP Address
                break

    address = public_ip
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
    exit(code)
