"""
Applies shell color escapes for pretty printing
"""
import os
import platform

DO_COLORS = True
# !! Windows compatibility for ANSI color codes !!
#
# If we're running on windows, we need to run the "color" command to enable
# ANSI color code support.
if platform.system() == "Windows":
    ver = platform.version()

    if "." in ver:
        ver = ver.split(".", 1)[0]

    try:
        verNum = int(ver)
    except ValueError:
        DO_COLORS = False

    # windows 10+ supports ANSI color codes after running the 'color' command to
    # properly set up the command prompt.  Older versions of windows do not, and
    # we should not attempt to use them there.
    if verNum >= 10:
        os.system("color")
    else:
        DO_COLORS = False


CLEAR_COLOR = "\x1b[0m"
COLOR_CODE_MAP = {
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "black": "\x1b[30m",
    "white": "\x1b[40m",
}


def colorize_string(string, color):
    """
    Returns the requested string, wrapped in ANSI color codes to colorize it as
    requested.  On platforms where colors are not supported, this just returns
    the string passed into it.
    """
    if not DO_COLORS:
        return string

    col = COLOR_CODE_MAP.get(color, CLEAR_COLOR)

    return f"{col}{string}{CLEAR_COLOR}"
