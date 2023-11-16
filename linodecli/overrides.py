"""
Contains wrappers for overriding certain pieces of command-handling logic.
This allows us to easily alter per-command outputs, etc. without making
large changes to the OpenAPI spec.
"""
from typing import Dict

from rich.align import Align
from rich.console import Console
from rich.table import Table

from linodecli.output import OutputMode

OUTPUT_OVERRIDES = {}


def output_override(command: str, action: str, output_mode: OutputMode):
    """
    A decorator function for adding a new output override handler.

    Output override functions should have the following signature::

        @output_override("command", "action", OutputMode.{output_mode})
        def my_override(operation, output_handler, json_data) -> bool:
            ...

    If the returned bool is False, the original output functionality will be skipped.
    Otherwise, the original output functionality will continue as normal.
    """

    def inner(func):
        OUTPUT_OVERRIDES[(command, action, output_mode)] = func

    return inner


@output_override("domains", "zone-file", OutputMode.delimited)
def handle_domains_zone_file(operation, output_handler, json_data) -> bool:
    # pylint: disable=unused-argument
    """
    Fix for output of 'linode-cli domains zone-file --text {id}'.
    """
    print("\n".join(json_data["zone_file"]))
    return False


@output_override("linodes", "types", OutputMode.table)
def handle_types_region_prices_list(
    operation, output_handler, json_data
) -> bool:
    """
    Override the output of 'linode-cli linodes types' to display regional pricing.
    """
    return linode_types_with_region_prices(operation, output_handler, json_data)


def linode_types_with_region_prices(
    operation, output_handler, json_data
) -> bool:
    # pylint: disable=unused-argument
    """
    Parse and reformat linode types output with region prices.
    """
    if len(json_data["data"]) < 1:
        return True

    output = Table()

    # To ensure the order of the headers and make sure we have region_prices as the last column
    headers = sorted(
        json_data["data"][0].keys() - ["addons", "price", "region_prices"],
        key=len,
    )
    headers += ["price.hourly", "price.monthly", "region_prices"]

    for header in headers:
        output.add_column(header, justify="center")

    for linode in json_data["data"]:
        row = []
        for h in headers:
            if h == "region_prices":
                sub_table = format_region_prices(linode[h])
                row.append(sub_table)

            elif h in ("price.hourly", "price.monthly"):
                price = format_prices(h, linode)
                row.append(Align(price, align="left"))

            else:
                row.append(Align(str(linode[h]), align="left"))

        output.add_row(*row)

    console = Console()
    console.print(output)

    print(
        "See our [Pricing Page](https://www.linode.com/pricing/) for Region-specific pricing, "
        + "which applies after migration is complete."
    )

    return False


def format_prices(prices, data: Dict[str, any]) -> any:
    """
    Format nested price entry.
    """
    price_headers = prices.split(".")

    return str(data[price_headers[0]][price_headers[1]])


def format_region_prices(data: Dict[str, any]) -> any:
    """
    Format nested region price entry into a sub-table.
    """
    subheaders = ["id", "hourly", "monthly"]

    sub_table = Table()

    for header in subheaders:
        sub_table.add_column(header, justify="center")

    for region_price in data:
        region_price_row = (
            Align(str(region_price[header]), align="left")
            for header in subheaders
        )
        sub_table.add_row(*region_price_row)

    return sub_table
