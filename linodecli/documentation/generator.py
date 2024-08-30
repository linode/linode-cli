"""
Contains the primary class for generating documentation files.
"""

import json
from dataclasses import asdict
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from linodecli import CLI
from linodecli.documentation.template_data import BuildMeta, Root

TEMPLATE_NAME_GROUP = "group.rst.j2"

OUTPUT_PATH_BUILD_META = "build_meta.json"
OUTPUT_PATH_GROUP_FORMAT = "groups/{name}.rst"


class DocumentationGenerator:
    """
    The primary class responsible for generating Linode CLI documentation.
    """

    def __init__(self):
        self._template_env = Environment(
            loader=PackageLoader("linodecli.documentation", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, cli: CLI, output_directory: str = "./docs/_generated"):
        """
        Generates the relevant documentation for the given CLI
        to the given `output_directory`.

        :param cli: The main Linode CLI object to generate documentation for.
        :param output_directory: The parent directory to generate the documentation under.
        """

        build_meta = BuildMeta(
            cli_version=cli.version,
            api_spec_version=cli.spec_version,
        )

        root_data = Root.from_cli(cli)

        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write the build data to a JSON file so it can be consumed from the
        # Sphinx config.
        with open(
            output_path / OUTPUT_PATH_BUILD_META, "w", encoding="utf-8"
        ) as f:
            json.dump(asdict(build_meta), f)

        # Generate a documentation file for each CLI group.
        for group in root_data.groups:
            output_path_group = output_path / OUTPUT_PATH_GROUP_FORMAT.format(
                name=group.name
            )
            output_path_group.parent.mkdir(parents=True, exist_ok=True)

            # Render & write the group documentation
            self._template_env.get_template(TEMPLATE_NAME_GROUP).stream(
                asdict(group), build_meta=build_meta
            ).dump(str(output_path_group))
