import re
import pytest

from tests.integration.helpers import exec_test_command

BASE_CMD = ["linode-cli", "kernels", "list", "--text", "--no-headers"]


class TestKernels:

    def test_list_available_kernels(self):
        process = exec_test_command(BASE_CMD + ["--format", "id"])
        output = process.stdout.decode()

        for line in output.splitlines():
            assert("linode" in line, "Output does not contain keyword linode..")

    def test_fields_from_kernels_list(self):
        process = exec_test_command(BASE_CMD + ["--delimiter", ',',
                                                "--format", 'id,version,kvm,architecture,pvops,deprecated,built'])
        output = process.stdout.decode()

        for line in output.splitlines():
            assert(re.search("linode/.*,.*,(False|True),(i386|x86_64),(False|True),(False|True),.*", line),
                   "Output does not match the format specified..")

    def test_view_kernel(self):
        process = exec_test_command(BASE_CMD + ["--format", "id"])
        output = process.stdout.decode()

        lines = output.splitlines()

        process = exec_test_command(["linode-cli", "kernels", "view", str(lines[0]), "--format",
                                     "id,version,kvm,architecture,pvops,deprecated,built",
                                     "--text", "--delimiter", ","])
        output = process.stdout.decode()

        assert("id,version,kvm,architecture,pvops,deprecated,built" in output, "No header found..")
        assert(re.search("linode/.*,.*,(False|True),(i386|x86_64),(False|True),(False|True),.*", output),
               "Ouput does not match the format specified..")
