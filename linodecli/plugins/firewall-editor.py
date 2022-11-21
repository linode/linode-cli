import argparse
import json
import re
import termios
import sys
from typing import Callable, Tuple, Any
from ipaddress import ip_address, IPv4Address

from terminaltables import PorcelainTable

BOLD = "\033[1m"
NOT_BOLD = "\033[0m"

# plugin-scoped variables
# setup terminal states
orig_term = termios.tcgetattr(sys.stdin.fileno())
new_term = termios.tcgetattr(sys.stdin.fileno())
# new terminal becomes unbuffered
new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)


class InputValidation:
    @staticmethod
    def input(input_text: str, validator: Callable[[str], None]):
        while True:
            value = input(input_text)
            try:
                validator(value)
            except ValueError as err:
                print("Invalid Input: {}".format("; ".join(err.args)))
                continue

            return value

    @staticmethod
    def input_io(rules):
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
        def callback(value):
            if value.strip() == "":
                return

            validator(value)

        return callback

    @staticmethod
    def int():
        def callback(value):
            if not value.isnumeric():
                raise ValueError("Expected an integer, got {}".format(value))

        return callback

    @staticmethod
    def index_of(ref_list, allow_append=False):
        def callback(value):
            if not value.isnumeric():
                raise ValueError("Expected an integer, got {}".format(value))

            value_int = int(value)

            if value_int < 0 or value_int >= len(ref_list) + (1 if allow_append else 0):
                raise ValueError("Invalid index {}".format(value_int))

        return callback

    @staticmethod
    def regex(pattern, error_msg):
        def callback(value):
            pattern_compiled = re.compile(pattern)

            if not re.fullmatch(pattern_compiled, value):
                raise ValueError(error_msg)

        return callback

    @staticmethod
    def one_of(valid_choices):
        def callback(value):
            if value.lower() not in [choice.lower() for choice in valid_choices]:
                raise ValueError("Invalid choice: {}; must be one of {}"
                                 .format(value, ', '.join(valid_choices)))

        return callback

    @staticmethod
    def ip_list():
        def callback(value):
            for ip in value.split(","):
                ip = ip.strip()

                # IP ranges are required
                ip_parts = ip.split('/')

                if len(ip_parts) != 2:
                    raise ValueError("Invalid IP: {}; IPs must be in IP/mask format.".format(ip))

                if not ip_parts[1].isnumeric():
                    raise ValueError("Invalid IP: {}; IP masks must be numeric".format(ip))

                try:
                    ip_address(ip_parts[0])
                except ValueError:
                    raise ValueError("Invalid IP: {}".format(ip))

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
    code, firewall = client.call_operation("firewalls", "view", args=[firewall_id])

    if code != 200:
        print("Error retrieving firewall: {}".format(code))
        sys.exit(1)

    code, rules = client.call_operation("firewalls", "rules-list", args=[firewall_id])

    if code != 200:
        print("Error retrieving firewall rules: {}".format(code))
        sys.exit(2)

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
        "{bold}Inbound Policy:{nobold} {inbound_policy}\t{bold}Outbound Policy:{nobold} {outbound_policy}".format(
            bold=BOLD,
            nobold=NOT_BOLD,
            inbound_policy=rules["inbound_policy"],
            outbound_policy=rules["outbound_policy"],
        )
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

    tab = PorcelainTable([header] + rows)
    tab.inner_heading_row_border = True
    print(tab.table)


def draw_rules(rules):
    """
    Draws the current rules
    """
    # clear the rules and below
    print("\033[3H\033[J", end="")

    print()
    print("{bold}Inbound Rules:{nobold}".format(bold=BOLD, nobold=NOT_BOLD))
    print_rules_table(rules["inbound"])
    print()
    print("{bold}Outbound Rules:{nobold}".format(bold=BOLD, nobold=NOT_BOLD))
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
    raise StopSave()


def quit(rules):
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
                InputValidation.index_of(change, allow_append=True))).strip()

        if ind_str == "":
            ind = len(change)
        else:
            ind = int(ind_str)

    label = InputValidation.input(
        "Rule Label (Optional): ",
        InputValidation.optional(InputValidation.regex(
            "^[a-zA-Z0-9\\-\\_\\.]{3,32}$",
            "Label must include only ASCII letters, numbers, underscores, periods, and dashes."))).strip()

    protocol = InputValidation.input(
        "Protocol (TCP/UDP/ICMP/IPENCAP): ",
        InputValidation.one_of({"TCP", "UDP", "ICMP", "IPENCAP"}))
    protocol = protocol.upper()

    action = InputValidation.input(
        "Action (ACCEPT/DROP): ", InputValidation.one_of({"ACCEPT", "DROP"}))
    action = action.upper()

    # Ports are now allowed for ICMP and IPENCAP protocols
    port = None

    if protocol not in ["ICMP", "IPENCAP"]:
        port = InputValidation.input(
            "Ports: ",
            InputValidation.regex(
                "^[0-9\\,\\- ]*$",
                "Input may be a single port, a range of ports, or a "
                "comma-separated list of single ports and port ranges."))

    addresses = InputValidation.input(
        "Addresses (comma separated): ",
        InputValidation.ip_list(),
    )

    addresses_ipv4 = []
    addresses_ipv6 = []

    for ip in addresses.split(','):
        ip = ip.strip()

        addresses_ipv4.append(ip) if type(ip_address(ip.split("/")[0])) is IPv4Address \
            else addresses_ipv6.append(ip)

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
        print("No entires to remove")
        return False

    ind_str = InputValidation.input(
        "Index to remove: ", InputValidation.optional(
            InputValidation.index_of(change))
    ).strip()

    # No changes to be made
    if ind_str == "":
        return False

    del change[int(ind_str)]

    return False


def swap_rules(rules):
    revert_terminal()

    change = InputValidation.input_io(rules)

    a_str = InputValidation.input(
        "Swap index: ", InputValidation.optional(
            InputValidation.index_of(change))).strip()

    if a_str == "":
        return False

    b_str = InputValidation.input(
        "With index: ", InputValidation.optional(
            InputValidation.index_of(change))).strip()

    if b_str == "":
        return False

    a, b = int(a_str), int(b_str)

    change[a], change[b] = change[b], change[a]

    return False


def toggle_policy(policy_key):
    def callback(rules):
        rules[policy_key] = "DROP" if rules[policy_key] == "ACCEPT" else "ACCEPT"

        return True

    return callback


ACTION_MAP = {
    "w": save_quit,
    "q": quit,
    "a": add_rule,
    "r": remove_rule,
    "s": swap_rules,
    "i": toggle_policy("inbound_policy"),
    "o": toggle_policy("outbound_policy")
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
    parser = argparse.ArgumentParser("firewall-editor", add_help=True)
    parser.add_argument('firewall_id', help="The ID of the firewall to edit.")
    parsed = parser.parse_args(args)

    # fetch the info and start going
    firewall, rules = _get_firewall(parsed.firewall_id, context.client)

    while True:
        save = mainloop(firewall, rules)

        # then update the rules
        if save:
            print("Saving Firewall configuration..")
            code, errors = context.client.call_operation("firewalls", "rules-update", args=[
                parsed.firewall_id,
                "--inbound", json.dumps(rules["inbound"]),
                "--outbound", json.dumps(rules["outbound"]),
                "--inbound_policy", rules["inbound_policy"],
                "--outbound_policy", rules["outbound_policy"],
            ])
            if code == 200:
                print("Rules updated successfully!")
                break
            else:
                print("Error editing rules: {}: {}".format(code, errors))
                # block to see the error, then re-enter the editor
                sys.stdin.read(1)
        else:
            print("Aborted.")
            break
