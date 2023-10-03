"""
The region-table plugin displays a table output
for the capabilities of each region.
"""
import sys

from rich.align import Align
from rich.console import Console
from rich.table import Table


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
        ("Block Storage", "Blocks"),
        ("Block Storage Migrations", "& Migration"),
    ]

    if status != 200:
        print("It failed :(")
        sys.exit(1)

    output = Table()
    headers = ["ID", "Label", "Loc"] + [x[1] for x in capabilities]
    for header in headers:
        output.add_column(header, justify="center")
    for region in regions["data"]:
        row = [
            Align(region["id"], align="left"),
            Align(region["label"], align="left"),
            region["country"].upper(),
        ] + [
            "✔" if c[0] in region["capabilities"] else "-" for c in capabilities
        ]
        output.add_row(*row)

    console = Console()
    console.print(output)
