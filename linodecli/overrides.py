"""
Contains wrappers for overriding certain pieces of command-handling logic.
This allows us to easily alter per-command outputs, etc. without making
large changes to the OpenAPI spec.
"""

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
