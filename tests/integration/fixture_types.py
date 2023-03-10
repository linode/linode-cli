"""
Complicated type alias for fixtures and other stuff.
"""
from pathlib import Path
from typing import Callable, List, Optional

GetTestFileType = Callable[[Optional[int], Optional[str]], List[Path]]
