"""
This module contains logic related to string parsing and replacement.
"""

import functools
import re
from html import unescape
from typing import List, Tuple

# Sentence delimiter, split on a period followed by any type of
# whitespace (space, new line, tab, etc.)
REGEX_SENTENCE_DELIMITER = re.compile(r"\.(?:\s|$)")

# Matches on pattern __prefix__ at the beginning of a description
# or after a comma
REGEX_TECHDOCS_PREFIX = re.compile(r"(?:, |\A)__([\w-]+)__")

# Matches on pattern [link title](https://.../)
REGEX_MARKDOWN_LINK = re.compile(r"\[(?P<text>.*?)]\((?P<link>.*?)\)")

MARKDOWN_RICH_TRANSLATION = [
    # Inline code blocks (e.g. `cool code`)
    (
        re.compile(
            r"`(?P<text>[^`]+)`",
        ),
        "italic deep_pink3 on grey15",
    ),
    # Bold tag (e.g. `**bold**` or `__bold__`)
    (
        re.compile(
            r"\*\*(?P<text>[^_\s]+)\*\*",
        ),
        "b",
    ),
    (
        re.compile(
            r"__(?P<text>[^_\s]+)__",
        ),
        "b",
    ),
    # Italics tag (e.g. `*italics*` or `_italics_`)
    (
        re.compile(
            r"\*(?P<text>[^*\s]+)\*",
        ),
        "i",
    ),
    (
        re.compile(
            r"_(?P<text>[^_\s]+)_",
        ),
        "i",
    ),
]


def markdown_to_rich_markup(markdown: str) -> str:
    """
    This function returns a version of the given argument description
    with the appropriate color tags.

    NOTE, Rich does support Markdown rendering, but it isn't suitable for this
    use-case quite yet due to some Group(...) padding issues and limitations
    with syntax themes.

    :param markdown: The argument description to colorize.
    :type markdown: str

    :returns: The translated Markdown
    """

    result = markdown

    for exp, style in MARKDOWN_RICH_TRANSLATION:
        result = exp.sub(
            # Necessary to avoid cell-var-in-loop linter fer
            functools.partial(
                lambda style, match: f"[{style}]{match['text']}[/]", style
            ),
            result,
        )

    return result


def extract_markdown_links(description: str) -> Tuple[str, List[str]]:
    """
    Extracts all Markdown links from the given description and
    returns them alongside the stripped description.

    :param description: The description of a CLI argument.
    :type description: str

    :returns: The stripped description and a list of extracted links.
    :rtype: Tuple[str, List[str]]
    """
    result_links = []

    def _sub_handler(match: re.Match) -> str:
        link = match["link"]
        if link.startswith("/"):
            link = f"https://linode.com{link}"

        result_links.append(link)
        return match["text"]

    result_description = REGEX_MARKDOWN_LINK.sub(_sub_handler, description)

    return result_description, result_links


def get_short_description(description: str) -> str:
    """
    Gets the first relevant sentence in the given description.

    :param description: The description of a CLI argument.
    :type description: str

    :returns: A single sentence from the description.
    :rtype: set
    """

    target_lines = description.splitlines()
    relevant_lines = None

    for i, line in enumerate(target_lines):
        # Edge case for descriptions starting with a note
        if line.lower().startswith("__note__"):
            continue

        relevant_lines = target_lines[i:]
        break

    if relevant_lines is None:
        raise ValueError(
            f"description does not contain any relevant lines: {description}",
        )

    return REGEX_SENTENCE_DELIMITER.split("\n".join(relevant_lines), 1)[0] + "."


def strip_techdocs_prefixes(description: str) -> str:
    """
    Removes all bold prefixes from the given description.

    :param description: The description of a CLI argument.
    :type description: str

    :returns: The stripped description
    :rtype: str
    """
    result_description = REGEX_TECHDOCS_PREFIX.sub(
        "", description.lstrip()
    ).lstrip()

    return result_description


def process_arg_description(description: str) -> Tuple[str, str]:
    """
    Processes the given raw request argument description into one suitable
    for help pages, etc.

    :param description: The original description for a request argument.
    :type description: str

    :returns: The description in Rich markup and original Markdown format.
    :rtype: Tuple[str, str]
    """

    if description == "":
        return "", ""

    result = get_short_description(description)
    result = strip_techdocs_prefixes(result)
    result = result.replace("\n", " ").replace("\r", " ")

    description, links = extract_markdown_links(result)

    if len(links) > 0:
        description += f" See: {'; '.join(links)}"

    return unescape(markdown_to_rich_markup(description)), unescape(description)
