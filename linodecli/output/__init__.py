"""
Output formatting module for CLI and plugins.
"""

from .helpers import (
    configure_output_handler,
    get_output_handler,
    register_output_args_shared,
)
from .output_handler import OutputHandler
