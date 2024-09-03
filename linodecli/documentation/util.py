"""
Contains various utility functions related to documentation generation.
"""

import math
import re
from typing import Optional

from linodecli.baked.parsing import REGEX_MARKDOWN_LINK

REGEX_MARKDOWN_CODE_TAG = re.compile(r"`(?P<text>[^`\s]+)`")
REGEX_USAGE_TOKEN = re.compile(r"(\[[^\[\]]+]|\S+)")
REGEX_PADDING_CHARACTER = re.compile(r"(^ +)", flags=re.M)

# Contains translations between OpenAPI data types and the condensed doc types.
OPENAPI_TYPE_FMT_TRANSLATION = {
    "string": "str",
    "boolean": "bool",
    "number": "float",
    "integer": "int",
}


def _normalize_padding(text: str, pad: str = "\t") -> str:
    """
    Normalizes the padding for the given text using the given pad character.

    :param text: The text to normalize.
    :param pad: The string to pad with.

    :returns: The normalized text.
    """

    text = text.replace("\t", "")

    padding_lengths = [
        len(match[0]) for match in REGEX_PADDING_CHARACTER.finditer(text)
    ]
    if len(padding_lengths) < 1:
        return text

    spaces_per_tab = min(padding_lengths)

    def _sub_handler(match: re.Match) -> str:
        match_length = len(match[0])

        return pad * math.floor(match_length / spaces_per_tab) + " " * (
            match_length % spaces_per_tab
        )

    return REGEX_PADDING_CHARACTER.sub(_sub_handler, text)


def _format_usage_text(text: str, max_length: int = 60, pad: str = "\t") -> str:
    """
    Formats the given usage text for use in the output documentation.

    :param text: The usage text to format.
    :param max_length: The maximum length of a line in the formatted output.
    :param pad: The string to pad lines with.

    :returns: The formatted usage text.
    """

    # Remove the prefix if it exists
    if text.startswith("usage: "):
        text = text[7:]

    # Apply text wrapping
    result = []
    current_line = []
    current_line_length = 0

    for token in REGEX_USAGE_TOKEN.finditer(text):
        token_len = len(token[0])

        # We've exceeded the maximum length, start a new line
        if current_line_length + len(token[0]) > max_length:
            result.append(current_line)
            current_line = []
            current_line_length = 0

        current_line.append(token[0])
        current_line_length += token_len

    # If the line has not already been appended, add it now
    if len(current_line) > 0:
        result.append(current_line)

    return "\n".join(
        [
            (pad * (1 if line > 0 else 0)) + " ".join(entries)
            for line, entries in enumerate(result)
        ]
    )


def __markdown_to_rst_sub_handler(match: re.Match) -> str:
    link = match["link"]
    if link.startswith("/"):
        link = f"https://linode.com{link}"

    return f"`{match['text']} <{link}>`_"


# TODO: Unify this with the markdown logic under a new `parsing` package.
def _markdown_to_rst(markdown_text: str) -> str:
    """
    Translates the given Markdown text into its RST equivalent.

    :param markdown_text: The Markdown text to translate.

    :returns: The translated text.
    """
    result = REGEX_MARKDOWN_LINK.sub(
        __markdown_to_rst_sub_handler, markdown_text
    )

    result = REGEX_MARKDOWN_CODE_TAG.sub(
        lambda match: f":code:`{match['text']}`", result
    )

    return result


def _format_type(
    data_type: str,
    item_type: Optional[str] = None,
    _format: Optional[str] = None,
) -> str:
    """
    Returns the formatted string for the given data and item types.

    :param data_type: The root type of an argument/attribute.
    :param item_type: The type of each item in an argument/attribute, if applicable.
    :param _format: The `format` attribute of an argument/attribute.

    :returns: The formatted type string,
    """

    if _format == "json" or data_type == "object":
        return "json"

    if data_type == "array":
        if item_type is None:
            raise ValueError(
                f"item_type must be defined when data_type is defined"
            )

        return f"[]{item_type}"

    type_fmt = OPENAPI_TYPE_FMT_TRANSLATION.get(data_type)
    if type_fmt is None:
        raise ValueError(f"Unknown data type: {data_type}")

    return type_fmt
