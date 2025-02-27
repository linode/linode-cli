"""
The object manipulation module of CLI Plugin for handling object storage
"""

import platform
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List

try:
    from boto3.exceptions import S3UploadFailedError
    from boto3.s3.transfer import MB, TransferConfig
except:
    # this has been handled in `call` function
    # by print an error message
    pass

from linodecli.exit_codes import ExitCodes
from linodecli.helpers import expand_globs
from linodecli.plugins import inherit_plugin_args
from linodecli.plugins.obj.config import (
    MULTIPART_UPLOAD_CHUNK_SIZE_DEFAULT,
    PLUGIN_BASE,
    PROGRESS_BAR_WIDTH,
)
from linodecli.plugins.obj.helpers import (
    ProgressPercentage,
    restricted_int_arg_type,
)


def upload_object(
    get_client, args, **kwargs
):  # pylint: disable=too-many-locals,unused-argument
    """
    Uploads an object to object storage
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " put"))

    parser.add_argument(
        "file", metavar="FILE", type=str, nargs="+", help="The files to upload."
    )
    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket to put a file in.",
    )
    parser.add_argument(
        "--acl-public",
        action="store_true",
        help="If set, the new object can be downloaded without "
        "authentication.",
    )
    parser.add_argument(
        "--chunk-size",
        type=restricted_int_arg_type(5120),
        default=MULTIPART_UPLOAD_CHUNK_SIZE_DEFAULT,
        help="The size of file chunks when uploading large files, in MB.",
    )

    # TODO:
    # 1. Allow user specified key (filename on cloud)
    # 2. As below:
    # parser.add_argument('--recursive', action='store_true',
    #                    help="If set, upload directories recursively.")

    parsed = parser.parse_args(args)
    client = get_client()

    to_upload: List[Path] = []
    files = list(parsed.file)
    for f in files:
        # Windows doesn't natively expand globs, so we should implement it here
        if platform.system() == "Windows" and "*" in f:
            results = expand_globs(f)
            files.extend(results)
            continue

    for f in files:
        file_path = Path(f).resolve()
        if not file_path.is_file():
            print(
                f"Error: '{file_path}' is not a valid file or does not exist.",
                file=sys.stderr,
            )
            sys.exit(ExitCodes.FILE_ERROR)

        to_upload.append(file_path)

    chunk_size = 1024 * 1024 * parsed.chunk_size

    prefix = None
    bucket = parsed.bucket
    if "/" in parsed.bucket:
        bucket = parsed.bucket.split("/")[0]
        prefix = parsed.bucket.removeprefix(f"{bucket}/")

    upload_options = {
        "Bucket": bucket,
        "Config": TransferConfig(multipart_chunksize=chunk_size * MB),
    }

    if parsed.acl_public:
        upload_options["ExtraArgs"] = {"ACL": "public-read"}

    for file_path in to_upload:
        print(f"Uploading {file_path.name}:")
        upload_options["Key"] = (
            file_path.name if not prefix else f"{prefix}/{file_path.name}"
        )
        upload_options["Filename"] = str(file_path.resolve())
        upload_options["Callback"] = ProgressPercentage(
            file_path.stat().st_size, PROGRESS_BAR_WIDTH
        )
        try:
            client.upload_file(**upload_options)
        except S3UploadFailedError as e:
            print(e, file=sys.stderr)
            sys.exit(ExitCodes.REQUEST_FAILED)

    print("Done.")


# We can't parse suppress_warnings from the parser
# because it is handled at the top-level of this plugin.
def get_object(
    get_client, args, suppress_warnings=False, **kwargs
):  # pylint: disable=unused-argument
    """
    Retrieves an uploaded object and writes it to a file
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " get"))

    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket the file is in."
    )
    parser.add_argument(
        "file", metavar="OBJECT", type=str, help="The object to retrieve."
    )
    parser.add_argument(
        "destination",
        metavar="LOCAL_FILE",
        type=str,
        nargs="?",
        help="The destination file. If omitted, uses the object "
        "name and saves to the current directory.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    # find destination file
    destination = parsed.destination

    if destination is None:
        destination = parsed.file

    destination = Path(destination).resolve()

    # download the file
    bucket = parsed.bucket
    key = parsed.file

    # Keys should always be relative
    if key.startswith("/"):
        if parsed.destination is None and not suppress_warnings:
            print(
                f'WARNING: This file will be saved to the absolute path "{key}".\n'
                "If you would like to store this file in a relative path, use the LOCAL_FILE "
                "parameter or remove the trailing slash character from the object name.",
                file=sys.stderr,
            )
        key = key[1:]

    destination_parent = destination.parent

    # In the future we should allow the automatic creation of parent directories
    if not destination_parent.exists():
        print(
            f"ERROR: Output directory {destination_parent} does not exist locally.",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.REQUEST_FAILED)

    response = client.head_object(
        Bucket=bucket,
        Key=key,
    )

    client.download_file(
        Bucket=bucket,
        Key=key,
        Filename=str(destination),
        Callback=ProgressPercentage(
            response.get("ContentLength", 0), PROGRESS_BAR_WIDTH
        ),
    )

    print("Done.")


def delete_object(
    get_client, args, **kwargs
):  # pylint: disable=unused-argument
    """
    Removes a file from a bucket
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " del"))

    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket to delete from."
    )
    parser.add_argument(
        "file", metavar="OBJECT", type=str, help="The object to remove."
    )

    parsed = parser.parse_args(args)
    client = get_client()
    bucket = parsed.bucket
    key = parsed.file

    client.delete_object(
        Bucket=bucket,
        Key=key,
    )

    print(f"{parsed.file} removed from {parsed.bucket}")
