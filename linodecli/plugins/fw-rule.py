from __future__ import print_function
import json
import argparse


def call(args, context):
    usage = """
    This plugin is for manipulating firewall rules one at a time,
    instead of editing the full firewall rule list

    Usage: linode-cli fw-rule [ACTION] [FIREWALL_ID] [RULE_LABEL] [RULE OPTIONS...]

    Examples:

        # Adding a rule to allow ssh traffic on TCP port 22 to all ipv4 addresses:
        linode-cli fw-rule add 12345 allow-ssh --tcp 22 --ipv4 all --accept
        # Editing the previous rule to only allow specific ip4 address range
        linode-cli fw-rule edit 12345 allow-ssh --ipv4 192.168.1.0/24 10.0.0.0/16
        # Showing the rule
        linode-cli fw-rule show 12345 allow-ssh
        # Removing the rule
        linode-cli fw-rule remove 12345 allow-ssh
        # Editing an outbound rule, changing policy from ACCEPT to DROP
        linode-cli fw-rule 12345 outbound-label --outbound --drop
    """

    parser = argparse.ArgumentParser("fw-rule", usage=usage, add_help=True)
    action_help = "The action to apply to the rule"
    action_choices = ("show", "add", "edit", "remove")
    parser.add_argument("ACTION", choices=action_choices, help=action_help)
    parser.add_argument("FIREWALL_ID", help="The id # of the firewall to edit")
    parser.add_argument("RULE_LABEL", help="The label/name of the firewall rule")

    rule_desc = """
    If adding a rule you must specify --protocol, --policy and at least one --ipv4 or --ipv6.
    TCP or UDP rules must also include --ports. 
    If editing a rule you may specify any number of rule options.
    If showing or removing a rule all other rule options are ignored
    """
    rule_opts = parser.add_argument_group(title="Rule options", description=rule_desc)

    for policy in ("accept", "drop"):
        arg_label = "--{}".format(policy)
        arg_help = "The {} policy will be applied to the rule".format(policy.upper())
        rule_opts.add_argument(
            arg_label,
            dest="policy",
            action="store_const",
            const=policy.upper(),
            help=arg_help,
        )

    for ip_type in ("4", "6"):
        arg_short = "-{}".format(ip_type)
        arg_long = "--ipv{}".format(ip_type)
        arg_help = (
            "List of ipv{0} ranges. Can be '--ipv{0} all' to include all addresses"
        )
        arg_help = arg_help.format(ip_type)
        rule_opts.add_argument(arg_short, arg_long, nargs="*", help=arg_help)

    protocols = rule_opts.add_mutually_exclusive_group()
    icmp_help = "Use ICMP protocol (do not specify ports)"
    protocols.add_argument("--icmp", action="store_true", help=icmp_help)
    ports_help = """
    Comma-separated list of {0} ports.
    Can include ranges (i.e --{0} 80,443,8000-8080)
    or 'all' to include all ports (shorthand for --{0} 1-65535)
    """
    for protocol in ("tcp", "udp"):
        arg_label = "--{}".format(protocol)
        arg_help = ports_help.format(protocol)
        protocols.add_argument(arg_label, help=arg_help)

    special = parser.add_argument_group(title="Special options")
    overwrite_help = """
    Allows the rule to be edited if it already exists (by comparing labels only).
    Adding a rule with a label that already exists will fail without this.
    Include this only when using the 'add' action
    """
    special.add_argument("--overwrite", action="store_true", help=overwrite_help)
    label_help = """
    Specify a new label / name for the rule.
    Include this only when using the 'edit' action
    """
    special.add_argument("--label", help=label_help)
    outbound_help = """
    Add this to manipulate outbound rules
    (Without this the default will use only inbound rules)
    """
    special.add_argument(
        "--outbound",
        dest="rule_type",
        action="store_const",
        const="outbound",
        default="inbound",
        help=outbound_help,
    )

    data = parser.parse_args(args)

    # Fixing protocol and ports to match the api
    data.protocol = None
    data.ports = None
    if data.icmp:
        data.protocol = "ICMP"
    elif data.tcp:
        data.protocol = "TCP"
        data.ports = data.tcp
    elif data.udp:
        data.protocol = "UDP"
        data.ports = data.udp
    # Fixing addresses to match the api
    if data.ipv4 and "all" in data.ipv4:
        data.ipv4 = ["0.0.0.0/0"]
    if data.ipv6 and "all" in data.ipv6:
        data.ipv6 = ["::/0"]
    data.addresses = {}
    if data.ipv4:
        data.addresses["ipv4"] = data.ipv4
    if data.ipv6:
        data.addresses["ipv6"] = data.ipv6

    # Validating input
    required = (data.addresses, data.protocol, data.policy)
    if data.ACTION == "add" and not all(required):
        exit("ERROR: Tried adding a rule without specifying ALL options")
    if data.ACTION == "edit" and not any(required + (data.label,)):
        exit("ERROR: Tried editing a rule without specifying ANY options")

    # Finally getting the firewall rule list and editing it
    res = context.client.call_operation("firewalls", "rules-list", [data.FIREWALL_ID])
    response, result = res
    if response != 200 or "errors" in result:
        print("Linode ERROR:")
        print(res)
        exit(1)
    existing_rules = result[data.rule_type]  # type: list
    existing_labels = [r["label"] for r in existing_rules]
    matching_labels_count = existing_labels.count(data.RULE_LABEL)
    if matching_labels_count > 1:
        error = "ERROR: Found more than one match for label {}, can't use this plugin"
        exit(error.format(data.RULE_LABEL))

    if data.ACTION == "show":
        if data.RULE_LABEL in existing_labels:
            matching_rules = [
                r for r in existing_rules if r["label"] == data.RULE_LABEL
            ]
            print(matching_rules[0])
        else:
            print("No match found (existing labels: {})".format(existing_labels))

    elif data.ACTION == "remove":
        new_rules = [r for r in existing_rules if r["label"] != data.RULE_LABEL]
        update_args = [
            data.FIREWALL_ID,
            "--{}".format(data.rule_type),
            json.dumps(new_rules),
        ]
        res = context.client.call_operation("firewalls", "rules-update", update_args)
        response, result = res
        if response != 200 or "errors" in result:
            print("Linode ERROR:")
            print(res)
            exit(1)
        else:
            success_msg = "Success: rule removed: {}"
            print(success_msg.format(data.RULE_LABEL))

    elif data.ACTION in ("add", "edit"):
        new_rules = existing_rules.copy()
        if data.overwrite or data.ACTION == "edit":
            # Remove the previous match, if any
            new_rules = [r for r in new_rules if r["label"] != data.RULE_LABEL]
        elif matching_labels_count > 0:
            error = "ERROR: Label {} already exits and --overwrite not specified"
            exit(error.format(data.RULE_LABEL))

        added_rule = dict(
            label=data.RULE_LABEL,
            action=data.policy,
            addresses=data.addresses,
            protocol=data.protocol,
            ports=data.ports,
        )

        if added_rule["protocol"] == "ICMP":
            added_rule.pop("ports")

        if data.ACTION == "edit":
            if data.RULE_LABEL not in existing_labels:
                error = "ERROR: Can't edit rule with label {}, this rule doesn't exist"
                exit(error.format(data.RULE_LABEL))
            previous_rule = [
                r for r in existing_rules if r["label"] == data.RULE_LABEL
            ][0]
            for key, value in added_rule.items():
                # Overwrite current None values with existing values
                if not value:
                    added_rule[key] = previous_rule[key]
            # If an edit of the label is needed
            added_rule["label"] = data.label or data.RULE_LABEL

        new_rules.append(added_rule)
        update_args = [
            data.FIREWALL_ID,
            "--{}".format(data.rule_type),
            json.dumps(new_rules),
        ]
        res = context.client.call_operation("firewalls", "rules-update", update_args)
        response, result = res
        if response != 200 or "errors" in result:
            print("Linode ERROR:")
            print(res)
            exit(1)
        else:
            success_msg = "Success: rule {}ed: {}"
            print(success_msg.format(data.ACTION, json.dumps(added_rule)))
