"""
The helper functions for the object storage plugin.
"""
from argparse import ArgumentTypeError
from datetime import datetime

from rich.table import Table
from rich.text import Text

from linodecli.plugins.obj.config import DATE_FORMAT


class ProgressPercentage:  # pylint: disable=too-few-public-methods
    """
    Progress bar class for boto3 file upload/download
    """

    def __init__(self, file_size: int, bar_width: int):
        self.size = file_size
        self.uploaded = 0
        self.bar_width = bar_width

    def __call__(self, bytes_amount: int):
        if bytes_amount == 0:
            return
        if not self.size:
            return
        self.uploaded += bytes_amount
        percentage = self.bar_width * (self.uploaded / self.size)
        progress = int(percentage)
        progress_bar = ("#" * progress) + ("-" * (self.bar_width - progress))
        print(f"\r |{progress_bar}| {percentage:.1f}%", end="\r")
        if self.uploaded == self.size:
            print()


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


def _convert_datetime(dt: datetime):
    """
    Given a string in INCOMING_DATE_FORMAT, returns a string in DATE_FORMAT
    """

    return dt.strftime(DATE_FORMAT)


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
    for unit in ("KB", "MB", "GB", "TB"):
        total = total / 1024
        if total < 1024:
            break
    return f"{round(total, 2)} {unit}"


# helper functions for output
def _borderless_table(data):
    """
    Returns a rich.Table object with no borders and correct padding
    """
    tab = Table.grid(padding=(0, 2, 0, 2))
    for row in data:
        row = [Text.from_ansi(str(item)) for item in row]
        tab.add_row(*row)

    return tab
