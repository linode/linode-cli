"""
Complicated type alias for fixtures and other stuff.
"""
from pathlib import Path
from typing import Callable, List, Optional

GetTestFilesType = Callable[[Optional[int], Optional[str]], List[Path]]
GetTestFileType = Callable[[Optional[str], Optional[str]], Path]
