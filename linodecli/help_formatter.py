"""
Contains sorting formatter for help menu.
"""

from argparse import HelpFormatter
from operator import attrgetter


class SortingHelpFormatter(HelpFormatter):
    """
    The formatter class for help menu.
    """

    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter("option_strings"))
        super().add_arguments(actions)
