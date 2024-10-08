"""
Plugin for CLI for editing firewalls
"""

import argparse
import json
import re
import sys
import termios
from ipaddress import IPv4Address, ip_address
from typing import Callable

from rich import box
from rich import print as rprint
from rich.table import Table

from linodecli.exit_codes import ExitCodes
from linodecli.plugins import inherit_plugin_args

BOLD = "\033[1m"
NOT_BOLD = "\033[0m"

# plugin-scoped variables
# setup terminal states
orig_term = termios.tcgetattr(sys.stdin.fileno())
new_term = termios.tcgetattr(sys.stdin.fileno())
# new terminal becomes unbuffered
new_term[3] = new_term[3] & ~termios.ICANON & ~termios.ECHO


class InputValidation:
    """
    Validating the input of firewalls
    """

    @staticmethod
    def input(input_text: str, validator: Callable[[str], None]):
        """
        Handle input from user
        """
        while True:
            value = input(input_text)
            try:
                validator(value)
            except ValueError as err:
                print(f"Invalid Input: {'; '.join(err.args)}", file=sys.stderr)
                continue

            return value

    @staticmethod
    def input_io(rules):
        """
        Handle input option between Inbound and Outbound
        """
        raw_terminal()

        print("[I]nbound or [O]utbound?")
        segment = " "
        while segment not in "io":
            segment = sys.stdin.read(1).lower()

        change = rules["inbound"]
        if segment == "o":
            change = rules["outbound"]

        revert_terminal()

        return change

    @staticmethod
    def optional(validator):
        """
        Handle optional value
        """

        def callback(value):
            if value.strip() == "":
                return

            validator(value)

        return callback

    @staticmethod
    def int():
        """
        Check if value is numeric
        """

        def callback(value):
            if not value.isnumeric():
                raise ValueError(f"Expected an integer, got {value}")

        return callback

    @staticmethod
    def index_of(ref_list, allow_append=False):
        """
        Validate index
        """

        def callback(value):
            if not value.isnumeric():
                raise ValueError(f"Expected an integer, got {value}")

            value_int = int(value)

            if value_int < 0 or value_int >= len(ref_list) + (
                1 if allow_append else 0
            ):
                raise ValueError(f"Invalid index {value_int}")

        return callback

    @staticmethod
    def regex(pattern, error_msg):
        """
        Regex callback
        """

        def callback(value):
            pattern_compiled = re.compile(pattern)

            if not re.fullmatch(pattern_compiled, value):
                raise ValueError(error_msg)

        return callback

    @staticmethod
    def one_of(valid_choices):
        """
        Validated choice is one of choices
        """

        def callback(value):
            if value.lower() not in [
                choice.lower() for choice in valid_choices
            ]:
                raise ValueError(
                    f"Invalid choice: {value}; must be one "
                    f"of {', '.join(valid_choices)}"
                )

        return callback

    @staticmethod
    def ip_list():
        """
        Callback for IP List
        """

        def callback(value):
            for ip in value.split(","):
                ip = ip.strip()

                # IP ranges are required
                ip_parts = ip.split("/")

                if len(ip_parts) != 2:
                    raise ValueError(
                        f"Invalid IP: {ip}; IPs must be in IP/mask format."
                    )

                if not ip_parts[1].isnumeric():
                    raise ValueError(
                        f"Invalid IP: {ip}; IP masks must be numeric"
                    )

                try:
                    ip_address(ip_parts[0])
                except ValueError as e:
                    raise ValueError(f"Invalid IP: {ip}") from e

        return callback


def raw_terminal():
    """
    Sets the terminal to new_term, in raw mode
    """
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, new_term)


def revert_terminal():
    """
    Sets the terminal to orig_term, as we found it
    """
    # and before we leave, reset to original terminal
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, orig_term)


##
# Helper functions
##


def _get_firewall(firewall_id, client):
    """
    Returns the firewall object with the given ID
    """
    code, firewall = client.call_operation(
        "firewalls", "view", args=[firewall_id]
    )

    if code != 200:
        print(f"Error retrieving firewall: {code}", file=sys.stderr)
        sys.exit(ExitCodes.FIREWALL_ERROR)

    code, rules = client.call_operation(
        "firewalls", "rules-list", args=[firewall_id]
    )

    if code != 200:
        print(f"Error retrieving firewall rules: {code}", file=sys.stderr)
        sys.exit(ExitCodes.FIREWALL_ERROR)

    return firewall, rules


##
# Drawing functions
##


def redraw(firewall, rules):
    """
    Clears the screen and redraws the firewall header
    """
    # clear the whole screen
    print("\033[H\033[J", end="")

    # print the title bar
    print(
        "{bold}Firewall:{nobold} {label}\t{bold}Status:{nobold} {status}".format(
            bold=BOLD,
            nobold=NOT_BOLD,
            label=firewall["label"],
            status=firewall["status"],
        )
    )
    print(
        f"{BOLD}Inbound Policy:{NOT_BOLD} {rules['inbound_policy']}\t"
        f"{BOLD}Outbound Policy:{NOT_BOLD} {rules['outbound_policy']}"
    )


def print_rules_table(rules):
    """
    Prints a table of rules to the screen with a given index offset
    """
    if len(rules) < 1:
        print("None")
        return

    header = ["#", "label", "protocol", "action", "ports", "addresses"]
    rows = []

    for ind, cur in enumerate(rules):
        addrs = []
        if "ipv4" in cur["addresses"]:
            addrs.extend(cur["addresses"]["ipv4"])

        if "ipv6" in cur["addresses"]:
            addrs.extend(cur["addresses"]["ipv6"])

        rows.append(
            [
                ind,
                cur["label"] if "label" in cur else "",
                cur["protocol"],
                cur["action"],
                cur["ports"] if "ports" in cur else "",
                ", ".join(addrs),
            ]
        )

    tab = Table(*header, box=box.ASCII, show_edge=False)
    for row in rows:
        row = [str(r) for r in row]
        tab.add_row(*row)
    rprint(tab)


def draw_rules(rules):
    """
    Draws the current rules
    """
    # clear the rules and below
    print("\033[3H\033[J", end="")

    print()
    print(f"{BOLD}Inbound Rules:{NOT_BOLD}")
    print_rules_table(rules["inbound"])
    print()
    print(f"{BOLD}Outbound Rules:{NOT_BOLD}")
    print_rules_table(rules["outbound"])


##
# Custom Exceptions
##


class StopDontSave(KeyboardInterrupt):
    """
    Excpetion that indicates that we shouldn't save changes; overrides KeyboardInterrupt
    so that ^C inherits this behavior
    """


class StopSave(Exception):
    """
    Custom exception class raised to break the main loop, saving when we're done
    """


##
# ACTIONS
##
# The signature of these is:
#
#    def action_name(rules: dict) -> bool:
#
# Where the incoming dict is the current state of the firewall rules (which will be
# modified), and the return value if whether or not we need to redraw the whole screen
##


def save_quit(rules):
    """
    Handle quitting with saving
    """
    raise StopSave()


def quit(rules):  # pylint: disable=redefined-builtin
    """
    Soft handle quitting without saving
    """
    raise StopDontSave()


def add_rule(rules):
    """
    Adds a new firewall rule
    """
    change = InputValidation.input_io(rules)

    ind = 0
    if len(change) > 0:
        ind_str = InputValidation.input(
            "Index (Optional): ",
            InputValidation.optional(
                InputValidation.index_of(change, allow_append=True)
            ),
        ).strip()

        if ind_str == "":
            ind = len(change)
        else:
            ind = int(ind_str)

    label = InputValidation.input(
        "Rule Label (Optional): ",
        InputValidation.optional(
            InputValidation.regex(
                "^[a-zA-Z0-9\\-\\_\\.]{3,32}$",
                "Label must include only ASCII letters, numbers, "
                + "underscores, periods, and dashes.",
            )
        ),
    ).strip()

    protocol = InputValidation.input(
        "Protocol (TCP/UDP/ICMP/IPENCAP): ",
        InputValidation.one_of({"TCP", "UDP", "ICMP", "IPENCAP"}),
    )
    protocol = protocol.upper()

    action = InputValidation.input(
        "Action (ACCEPT/DROP): ", InputValidation.one_of({"ACCEPT", "DROP"})
    )
    action = action.upper()

    # Ports are now allowed for ICMP and IPENCAP protocols
    port = None

    if protocol not in ["ICMP", "IPENCAP"]:
        port = InputValidation.input(
            "Ports: ",
            InputValidation.regex(
                "^[0-9\\,\\- ]*$",
                "Input may be a single port, a range of ports, or a "
                "comma-separated list of single ports and port ranges.",
            ),
        )

    addresses = InputValidation.input(
        "Addresses (comma separated): ",
        InputValidation.ip_list(),
    )

    addresses_ipv4 = []
    addresses_ipv6 = []

    for ip in addresses.split(","):
        ip = ip.strip()

        if (
            type(ip_address(ip.split("/")[0])) is IPv4Address
        ):  # pylint: disable=unidiomatic-typecheck
            addresses_ipv4.append(ip)
        else:
            addresses_ipv6.append(ip)

    # make the new rule
    new_rule = {
        "protocol": protocol,
        "addresses": {},
        "action": action,
    }

    # Ports are rejected for ICMP and IPENCAP protocols
    if port is not None:
        new_rule["ports"] = port

    # The API will reject empty lists, let's make sure
    # they're only included if necessary
    if len(addresses_ipv4) > 0:
        new_rule["addresses"]["ipv4"] = addresses_ipv4

    if len(addresses_ipv6) > 0:
        new_rule["addresses"]["ipv6"] = addresses_ipv6

    if label:
        # this field must be omitted unless it is set
        new_rule["label"] = label

    change.insert(ind, new_rule)

    return False


def remove_rule(rules):
    """
    Removes a rule (by index)
    """
    change = InputValidation.input_io(rules)

    if len(change) < 1:
        print("No entires to remove", file=sys.stderr)
        return False

    ind_str = InputValidation.input(
        "Index to remove: ",
        InputValidation.optional(InputValidation.index_of(change)),
    ).strip()

    # No changes to be made
    if ind_str == "":
        return False

    del change[int(ind_str)]

    return False


def swap_rules(rules):
    """
    Swap index rules
    """
    revert_terminal()

    change = InputValidation.input_io(rules)

    a_str = InputValidation.input(
        "Swap index: ",
        InputValidation.optional(InputValidation.index_of(change)),
    ).strip()

    if a_str == "":
        return False

    b_str = InputValidation.input(
        "With index: ",
        InputValidation.optional(InputValidation.index_of(change)),
    ).strip()

    if b_str == "":
        return False

    a, b = int(a_str), int(b_str)

    change[a], change[b] = change[b], change[a]

    return False


def toggle_policy(policy_key):
    """
    Callback for toggling policy
    """

    def callback(rules):
        rules[policy_key] = (
            "DROP" if rules[policy_key] == "ACCEPT" else "ACCEPT"
        )

        return True

    return callback


ACTION_MAP = {
    "w": save_quit,
    "q": quit,
    "a": add_rule,
    "r": remove_rule,
    "s": swap_rules,
    "i": toggle_policy("inbound_policy"),
    "o": toggle_policy("outbound_policy"),
}


##
# Logic
##


def get_action():
    """
    Prints the action prompt and returns the action to run
    """
    print()
    print("Rules: [A]dd, [R]emove, or [S]wap")
    print("Policy: Toggle [I]nbound or [O]utbound")
    print("[W]rite settings or [Q]uit")

    selection = " "

    while selection.lower() not in ACTION_MAP:
        selection = sys.stdin.read(1)

    return ACTION_MAP[selection.lower()]


def mainloop(firewall, rules):
    """
    Accepts a firewall and the current ruleset and loops until told to be done
    allowing the rules to be modified.
    """
    full_redraw = True
    save = False

    while True:
        try:
            if full_redraw:
                redraw(firewall, rules)
                full_redraw = False

            draw_rules(rules)

            raw_terminal()
            action = get_action()

            full_redraw = action(rules)
        except StopSave:
            save = True
            break
        except StopDontSave:
            break

    revert_terminal()

    return save


def call(args, context):
    """
    Invokes the Interactive Firewall Plugin
    """
    parser = inherit_plugin_args(
        argparse.ArgumentParser("firewall-editor", add_help=True)
    )
    parser.add_argument("firewall_id", help="The ID of the firewall to edit.")

    parsed = parser.parse_args(args)

    # fetch the info and start going
    firewall, rules = _get_firewall(parsed.firewall_id, context.client)

    while True:
        save = mainloop(firewall, rules)

        # then update the rules
        if save:
            print("Saving Firewall configuration..")
            code, errors = context.client.call_operation(
                "firewalls",
                "rules-update",
                args=[
                    parsed.firewall_id,
                    "--inbound",
                    json.dumps(rules["inbound"]),
                    "--outbound",
                    json.dumps(rules["outbound"]),
                    "--inbound_policy",
                    rules["inbound_policy"],
                    "--outbound_policy",
                    rules["outbound_policy"],
                ],
            )
            if code == 200:
                print("Rules updated successfully!")
                break
            print(f"Error editing rules: {code}: {errors}", file=sys.stderr)
            # block to see the error, then re-enter the editor
            sys.stdin.read(1)
        else:
            print("Aborted.", file=sys.stderr)
            break
