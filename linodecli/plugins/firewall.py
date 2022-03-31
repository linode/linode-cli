import argparse
import json
import termios
import sys

from terminaltables import PorcelainTable


BOLD = "\033[1m"
NOT_BOLD = "\033[0m"


# plugin-scoped variables
# setup terminal states
orig_term = termios.tcgetattr(sys.stdin.fileno())
new_term = termios.tcgetattr(sys.stdin.fileno())
# new terminal becomes unbuffered
new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)


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


def print_rules_table(rules, offset=0):
    """
    Prints a table of rules to the screen with a given index offset
    """
    if len(rules) < 1:
        print("None")
        return

    header = ["ind", "label", "protocol", "action", "ports", "addresses"]
    rows = []

    for ind, cur in enumerate(rules):
        addrs = ", ".join(
                (cur["addresses"]["ipv4"] if "ipv4" in cur["addresses"] else cur["addresses"]["ipv6"])
        )
        rows.append(
            [
                ind+offset,
                cur["label"] if "label" in cur else "",
                cur["protocol"],
                cur["action"],
                cur["ports"] if "ports" in cur else "",
                addrs,
            ]
        )

    tab = PorcelainTable([header]+rows)
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
    print_rules_table(rules["outbound"], len(rules["inbound"]))


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

def toggle_inbound_policy(rules):
    """
    Updates inbound policy and calls for full redraw
    """
    if rules["inbound_policy"] == "ACCEPT":
        rules["inbound_policy"] = "DROP"
    else:
        rules["inbound_policy"] = "ACCEPT"

    return True


def toggle_outbound_policy(rules):
    """
    Updates outbound policy and calls for full redraw
    """
    if rules["outbound_policy"] == "ACCEPT":
        rules["outbound_policy"] = "DROP"
    else:
        rules["outbound_policy"] = "ACCEPT"

    return True


def save_quit(rules):
    raise StopSave()


def quit(rules):
    raise StopDontSave()


def add_rule(rules):
    """
    Adds a new firewall rule
    """
    print("[I]nbound or [O]utbound?")
    segment = " "
    while segment not in "io":
        segment = sys.stdin.read(1).lower()

    revert_terminal()
    
    # TODO - generic functions for these, and autocomplete long strings (i.e. "accept" for "a" or "acc")
    while True:
        ind = input("Index: ")
        try:
            ind = int(ind)
            break
        except ValueError:
            continue

    label = input("Label: ")

    protocol = " "

    while protocol not in ("TCP","UDP"):
        protocol = input("Protocol (TCP/UDP): ").upper()

    action = " "
    while action not in ("ACCEPT", "DROP"):
        action = input("Action (ACCEPT/DROP): ").upper()

    port = input("Port: ")

    addresses = [c.strip() for c in input("Addresses (comma serparated): ").split(",")]

    # do it
    change = rules["inbound"]
    if segment == "o":
        change = rules["outbound"]
        ind -= len(rules["inbound"])

    # make the new rule
    new_rule = {
        "ports": port,
        "protocol": protocol,
        "addresses": {
            "ipv4": addresses, # TODO handle v6 and validating addresses
        },
        "action": action,
    }

    if label:
        # this field must be omitted unless it is set
        new_rule["label"] = label

    # TODO - insert at index
    change.append(new_rule)

    return False


def remove_rule(rules):
    """
    Removes a rule (by index)
    """
    revert_terminal()

    ind = input("Index to remove: ")

    try:
        ind = int(ind)
    except ValueError:
        return False

    change = rules["inbound"]
    if ind >= len(rules["inbound"]):
        change = rules["outbound"]
        ind -= len(rules["inbound"])

    if ind >= 0 and ind < len(change):
        del change[ind]

    return False


def swap_rules(rules):
    revert_terminal()

    a = input("Swap index: ")
    b = input("With index: ")

    try:
        a = int(a)
        b = int(b)
    except ValueError:
        return False

    change = rules["inbound"]
    if a < len(change) and b >= len(change):
        # can't swap between inbound and outbound
        return False

    if a >= len(change):
        change = rules["outbound"]
        a -= len(rules["inbound"])
        b -= len(rules["inbound"])

    tmp = change[a]
    change[a] = change[b]
    change[b] = tmp

    return False


ACTION_MAP = {
    "i": toggle_inbound_policy,
    "o": toggle_outbound_policy,
    "w": save_quit,
    "q": quit,
    "a": add_rule,
    "r": remove_rule,
    "s": swap_rules,
}

##
# Logic
##

def get_action():
    """
    Prints the action prompt and returns the action to run
    """
    print()
    print("Global: Toggle [I]nbound or [O]utbound Policy")
    print("Rules: [A]dd, [R]emove, or [S]wap")
    print("[W]rtie settings or [Q]uit")

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
    parser = argparse.ArgumentParser("firewall", add_help=True)
    parser.add_argument('firewall_id', help="The ID of the firewall to edit.")
    parsed = parser.parse_args(args)

    
    # fetch the info and start going
    firewall, rules = _get_firewall(parsed.firewall_id, context.client)


    while True:
        save = mainloop(firewall, rules)

        # then update the rules
        if save:
            print("Saving..")
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
