"""
The region-table plugin displays a table output
for the capabilities of each region.
"""
import sys

from prettytable import PrettyTable


def call(_, ctx):
    """
    Invokes the region-table plugin
    """
    status, regions = ctx.client.call_operation("regions", "list")
    capabilities_short = [
        "Linodes",
        "GPU",
        "Premium",
        "NB",
        "Blocks",
        "Objects",
        "K8s",
        "FW",
        "Vlans",
        "DB",
    ]
    capabilities = [
        "Linodes",
        "GPU Linodes",
        "Premium Plans",
        "NodeBalancers",
        "Block Storage",
        "Object Storage",
        "Kubernetes",
        "Cloud Firewall",
        "Vlans",
        "Managed Databases",
    ]

    if status != 200:
        print("It failed :(")
        sys.exit(1)

    output = PrettyTable()
    output.field_names = ["ID", "Label", "Loc"] + capabilities_short
    output.align = "c"
    for region in regions["data"]:
        row = [region["id"], region["label"], region["country"].upper()] + [
            "✔" if c in region["capabilities"] else "-" for c in capabilities
        ]
        output.add_row(row)

    print(output)
