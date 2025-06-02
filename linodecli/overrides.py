"""
Contains wrappers for overriding certain pieces of command-handling logic.
This allows us to easily alter per-command outputs, etc. without making
large changes to the OpenAPI spec.
"""

from typing import Dict, List

from rich import box
from rich import print as rprint
from rich.align import Align
from rich.console import Console
from rich.table import Table
from rich.theme import Theme

from linodecli.output.output_handler import OutputMode

OUTPUT_OVERRIDES = {}

REPLICA_STATUS_THEME = {
    "available": "bright_green",
    "creating": "bright_yellow",
    "pending": "yellow",
    "pending replication": "yellow",
    "pending deletion": "red",
    "replicating": "bright_yellow",
}


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


@output_override("databases", "mysql-config-view", OutputMode.table)
def handle_databases_mysql_config_view(
    operation, output_handler, json_data
) -> bool:
    # pylint: disable=unused-argument
    """
    Override the output of 'linode-cli databases mysql-config-view'
    to properly display the mysql engine config.
    """
    return databases_mysql_config_view_output(json_data)


@output_override("databases", "postgres-config-view", OutputMode.table)
def handle_databases_postgres_config_view(
    operation, output_handler, json_data
) -> bool:
    # pylint: disable=unused-argument
    """
    Override the output of 'linode-cli databases postgres-config-view'
    to properly display the postgresql engine config.
    """
    return databases_postgres_config_view_output(json_data)


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


@output_override("images", "replicate", OutputMode.table)
def handle_image_replicate(operation, output_handler, json_data) -> bool:
    # pylint: disable=unused-argument
    """
    Override the output of 'linode-cli images replicate'.
    """
    return image_replicate_output(json_data)


@output_override("placement", "group-view", OutputMode.table)
def handle_placement_group_view(operation, output_handler, json_data) -> bool:
    # pylint: disable=unused-argument
    """
    Override the output of 'linode-cli placement group-view' to show PG members.
    """
    return pg_view_output(json_data)


@output_override("placement", "group-update", OutputMode.table)
def handle_placement_group_update(operation, output_handler, json_data) -> bool:
    # pylint: disable=unused-argument
    """
    Override the output of 'linode-cli placement group-update' to show PG members.
    """
    return pg_view_output(json_data)


@output_override("placement", "assign-linode", OutputMode.table)
def handle_placement_assign_linode(
    operation, output_handler, json_data
) -> bool:
    # pylint: disable=unused-argument
    """
    Override the output of 'linode-cli placement assign-linode' to show PG members.
    """
    return pg_view_output(json_data)


@output_override("placement", "unassign-linode", OutputMode.table)
def handle_placement_unassign_linode(
    operation, output_handler, json_data
) -> bool:
    # pylint: disable=unused-argument
    """
    Override the output of 'linode-cli placement unassign-linode' to show PG members.
    """
    return pg_view_output(json_data)


def linode_types_with_region_prices(
    operation, output_handler, json_data
) -> bool:
    # pylint: disable=unused-argument
    """
    Parse and reformat linode types output with region prices.
    """
    if len(json_data["data"]) < 1:
        return True

    output = Table(
        header_style="bold",
        show_lines=True,
    )

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

    rprint(
        "[cyan]See our [Pricing Page](https://www.linode.com/pricing/) "
        "for Region-specific pricing, "
        "which applies after migration is complete."
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

    sub_table = Table(box=box.SIMPLE_HEAVY)

    for header in subheaders:
        sub_table.add_column(header, justify="center")

    for region_price in data:
        region_price_row = (
            Align(str(region_price[header]), align="left")
            for header in subheaders
        )
        sub_table.add_row(*region_price_row)

    return sub_table


def build_replicas_output(replicas: List) -> Table:
    """
    Format nested replicas list to a sub-table.
    """
    replicas_output = Table(show_header=False, box=None)
    replicas_headers = replicas[0].keys()
    for replica in replicas:
        row = []
        for h in replicas_headers:
            if h == "status" and replica[h] in REPLICA_STATUS_THEME:
                row.append(
                    Align(str(replica[h]), align="left", style=replica[h])
                )
            else:
                row.append(Align(str(replica[h]), align="left"))
        replicas_output.add_row(*row)

    return replicas_output


def image_replicate_output(json_data) -> bool:
    """
    Parse and format the image replicate output table.
    """
    console = Console(theme=Theme(REPLICA_STATUS_THEME))

    output = Table(
        header_style="bold",
        show_lines=True,
    )

    row = []
    headers = ["id", "label", "status", "total_size", "regions"]
    for header in headers:
        if header in json_data:
            if header == "regions" and len(json_data[header]) > 0:
                # leverage `replicas` in output for readability
                output.add_column("replicas", justify="center")
                row.append(build_replicas_output(json_data[header]))
            elif json_data[header] is not None:
                output.add_column(header, justify="center")
                row.append(Align(str(json_data[header]), align="left"))

    output.add_row(*row)

    console.print(output)

    return False


def build_pg_members(members: List) -> Table:
    """
    Format nested linode members list to a sub-table.
    """
    table = Table()

    member_headers = members[0].keys()
    for h in member_headers:
        table.add_column(h, justify="center")

    for member in members:
        row = []
        for h in member_headers:
            row.append(Align(str(member[h]), align="left"))
        table.add_row(*row)

    return table


def pg_view_output(json_data) -> bool:
    """
    Parse and format the placement group output table.
    """
    output = Table(
        header_style="bold",
        show_lines=True,
    )

    row = []
    for header in json_data:
        if json_data[header] is not None:
            output.add_column(header, justify="center")
            if header == "members" and len(json_data[header]) > 0:
                row.append(build_pg_members(json_data[header]))
            else:
                row.append(Align(str(json_data[header]), align="left"))

    output.add_row(*row)

    console = Console()
    console.print(output)

    return False


def add_param_row(output, param_name, param_data):
    """
    Construct and add a row to the output table for DB Config view overrides.
    """
    param_type = str(param_data.get("type", ""))
    example = str(param_data.get("example", ""))
    minimum = str(param_data.get("minimum", ""))
    maximum = str(param_data.get("maximum", ""))
    min_length = str(param_data.get("minLength", ""))
    max_length = str(param_data.get("maxLength", ""))
    pattern = str(param_data.get("pattern", ""))
    requires_restart = "YES" if param_data.get("requires_restart") else "NO"
    description = param_data.get("description", "")

    output.add_row(
        param_name,
        param_type,
        example,
        minimum,
        maximum,
        min_length,
        max_length,
        pattern,
        requires_restart,
        Align(description, align="left"),
    )


def databases_mysql_config_view_output(json_data) -> bool:
    """
    Parse and format the MySQL configuration output table.
    """
    output = Table(header_style="bold", show_lines=True)

    output.add_column("Parameter", style="bold")
    output.add_column("Type", justify="center")
    output.add_column("Example", justify="center")
    output.add_column("Min", justify="center")
    output.add_column("Max", justify="center")
    output.add_column("Min Length", justify="center")
    output.add_column("Max Length", justify="center")
    output.add_column("Pattern", justify="center")
    output.add_column("Requires Restart", justify="center")
    output.add_column("Description", style="dim")

    for field, params in json_data.items():
        if field in ["binlog_retention_period"]:
            add_param_row(output, field, params)
        else:
            for key, val in params.items():
                param_name = f"{field}.{key}"
                add_param_row(output, param_name, val)

    console = Console()
    console.print(output)

    return False


def databases_postgres_config_view_output(json_data) -> bool:
    """
    Parse and format the PostgreSQL configuration output table.
    """
    output = Table(header_style="bold", show_lines=True)

    output.add_column("Parameter", style="bold")
    output.add_column("Type", justify="center")
    output.add_column("Example", justify="center")
    output.add_column("Min", justify="center")
    output.add_column("Max", justify="center")
    output.add_column("Min Length", justify="center")
    output.add_column("Max Length", justify="center")
    output.add_column("Pattern", justify="center")
    output.add_column("Requires Restart", justify="center")
    output.add_column("Description", style="dim")

    for field, params in json_data.items():
        if field in [
            "pg_stat_monitor_enable",
            "shared_buffers_percentage",
            "work_mem",
        ]:
            add_param_row(output, field, params)
        else:
            for key, val in params.items():
                param_name = f"{field}.{key}"
                add_param_row(output, param_name, val)

    console = Console()
    console.print(output)

    return False
