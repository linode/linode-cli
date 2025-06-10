import os
import tempfile

import pytest

# A minimal gzipped image that will be accepted by the API
TEST_IMAGE_CONTENT = (
    b"\x1f\x8b\x08\x08\xbd\x5c\x91\x60\x00\x03\x74\x65\x73\x74\x2e\x69"
    b"\x6d\x67\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)


@pytest.fixture(scope="session", autouse=True)
def fake_image_file():
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        fp.write(TEST_IMAGE_CONTENT)
        file_path = fp.name

    yield file_path

    os.remove(file_path)
