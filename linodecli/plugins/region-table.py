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

    capabilities = [
        ("Linodes", "Linodes"),
        ("GPU Linodes", "GPU"),
        ("NodeBalancers", "NB"),
        ("Kubernetes", "K8s"),
        ("Firewalls", "FW"),
        ("Managed Databases", "DB"),
        ("Object Storage", "OBJ"),
        ("Vlans", "Vlan"),
        ("Premium Plans", "Premium"),
        ("Metadata", "Meta"),
        ("Bare Metal", "Metal"),
        ("Block Storage", "Blocks"),
        ("Block Storage Migrations", "& Migration"),
    ]

    if status != 200:
        print("It failed :(")
        sys.exit(1)

    output = PrettyTable()
    output.field_names = ["ID", "Label", "Loc"] + [x[1] for x in capabilities]
    output.align = "c"
    for region in regions["data"]:
        row = [region["id"], region["label"], region["country"].upper()] + [
            "✔" if c[0] in region["capabilities"] else "-" for c in capabilities
        ]
        output.add_row(row)

    print(output)
