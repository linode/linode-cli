"""
Helpers for CLI output arguments and OutputHandler.
"""

from argparse import ArgumentParser, Namespace

from linodecli.output.output_handler import OutputHandler


def register_output_args_shared(parser: ArgumentParser):
    """
    Add output formatting related arguments to the ArgumentParser.
    """
    parser.add_argument(
        "--text",
        action="store_true",
        help="Display text output with a delimiter (defaults to tabs).",
    )
    parser.add_argument(
        "--delimiter",
        metavar="DELIMITER",
        type=str,
        help="The delimiter when displaying raw output.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Display output as JSON."
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Display output in Markdown format.",
    )

    parser.add_argument(
        "--ascii-table",
        action="store_true",
        help="Display output in an ASCII table.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="If set, pretty-print JSON output.",
    )
    parser.add_argument(
        "--no-headers",
        action="store_true",
        help="If set, does not display headers in output.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Deprecated flag. An alias of '--all-columns', "
            "scheduled to be removed in a future version."
        ),
    )
    parser.add_argument(
        "--all-columns",
        action="store_true",
        help=(
            "If set, displays all possible columns instead of "
            "the default columns. This may not work well on some terminals."
        ),
    )
    parser.add_argument(
        "--format",
        metavar="FORMAT",
        type=str,
        help="The columns to display in output. Provide a comma-"
        "separated list of column names.",
    )
    parser.add_argument(
        "--no-truncation",
        action="store_true",
        default=False,
        help="Prevent the truncation of long values in command outputs.",
    )
    parser.add_argument(
        "--single-table",
        action="store_true",
        help="Disable printing multiple tables for complex API responses.",
    )
    parser.add_argument(
        "--table",
        type=str,
        action="append",
        help="The specific table(s) to print in output of a command.",
    )
    parser.add_argument(
        "--column-width",
        type=int,
        default=None,
        help="Sets the maximum width of each column in outputted tables. "
        "By default, columns are dynamically sized to fit the terminal.",
    )


def get_output_handler(parsed: Namespace, suppress_warnings: bool = False):
    """
    Create a new OutputHandler and configure it with the parsed arguments.
    """
    output_handler = OutputHandler()
    output_handler.configure(parsed, suppress_warnings)
