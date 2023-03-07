"""
The helper functions for the object storage plugin.
"""

from argparse import ArgumentTypeError
from datetime import datetime

from terminaltables import SingleTable

from linodecli.plugins.obj.config import DATE_FORMAT, INCOMING_DATE_FORMAT


def _progress(cur: float, total: float):
    """
    Draws the upload progress bar.
    """
    # We can't divide by zero :)
    if total == 0.0:
        return

    percent = f"{100 * (cur / float(total)):.1f}"
    progress = int(100 * cur // total)
    progress_bar = ("#" * progress) + ("-" * (100 - progress))
    print(f"\r |{progress_bar}| {percent}%", end="\r")

    if cur == total:
        print()


def restricted_int_arg_type(
    max: int, min: int = 1
):  # pylint: disable=redefined-builtin
    """
    An ArgumentParser arg type for integers that restricts the value to between `min` and `max`
    (inclusive for both.)
    """

    def restricted_int(string: str):
        err_msg = f"Value must be an integer between {min} and {max}"
        try:
            value = int(string)
        except ValueError as e:
            # argparse can handle ValueErrors, but shows an unfriendly "invalid restricted_int
            # value: '0.1'" message, so catch and raise with a better message.
            raise ArgumentTypeError(err_msg) from e
        if value < min or value > max:
            raise ArgumentTypeError(err_msg)
        return value

    return restricted_int


def _convert_datetime(dt: str):
    """
    Given a string in INCOMING_DATE_FORMAT, returns a string in DATE_FORMAT
    """
    return datetime.strptime(dt, INCOMING_DATE_FORMAT).strftime(DATE_FORMAT)


def _pad_to(
    val, length=10, right_align=False
):  # pylint: disable=unused-argument
    """
    Pads val to be at minimum length characters long
    """
    ret = str(val)
    padding = ""

    if len(ret) < 10:
        padding = " " * (10 - len(ret))

    if right_align:
        ret = padding + ret
    else:
        ret = ret + padding

    return ret


def _denominate(total):
    """
    Coverts bucket size to human readable bytes.
    """
    total = float(total)
    denomination = ["KB", "MB", "GB", "TB"]
    for x in denomination:
        if total > 1024:
            total = total / 1024
        if total < 1024:
            total = round(total, 2)
            total = str(total) + " " + x
            break
    return total


# helper functions for output
def _borderless_table(data):
    """
    Returns a terminaltables.SingleTable object with no borders and correct padding
    """
    tab = SingleTable(data)
    tab.inner_heading_row_border = False
    tab.inner_column_border = False
    tab.outer_border = False
    tab.padding_left = 0
    tab.padding_right = 2

    return tab
