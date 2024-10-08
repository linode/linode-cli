import json
from pathlib import Path

DOCS_PATH = Path(__file__).parent.resolve()
BUILD_META_PATH = DOCS_PATH / "_generated" / "build_meta.json"

if not BUILD_META_PATH.is_file():
    raise FileNotFoundError(
        "Could not find build_meta file. "
        "Was `linode-cli generate-docs` run before attempting to render this documentation?",
    )

with open(BUILD_META_PATH, "r") as f:
    build_meta = json.load(f)

# Project information
project = "linode-cli"
copyright = "2024, Akamai Technologies Inc."
author = "Akamai Technologies Inc."
version = f"v{build_meta.get('cli_version')} (API v{build_meta.get('api_spec_version')})"

# General configuration
extensions = ["sphinx_rtd_theme"]
source_suffix = ".rst"
exclude_patterns = []
highlight_language = "bash"
templates_path = ["templates"]

# HTML builder configuration
html_logo = "static/logo.svg"
html_favicon = "static/favicon.ico"
html_static_path = ["static"]
html_css_files = [
    "overlay.css"
]

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "style_nav_header_background": "#009CDE"
}
