"""
The object manipulation module of CLI Plugin for handling object storage
"""
import platform
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from boto3.exceptions import S3UploadFailedError
from boto3.s3.transfer import MB, TransferConfig

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


def upload_object(get_client, args):  # pylint: disable=too-many-locals
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
            sys.exit(f"No file {file_path}")

        to_upload.append(file_path)

    chunk_size = 1024 * 1024 * parsed.chunk_size

    upload_options = {
        "Bucket": parsed.bucket,
        "Config": TransferConfig(multipart_chunksize=chunk_size * MB),
    }

    if parsed.acl_public:
        upload_options["ExtraArgs"] = {"ACL": "public-read"}

    for file_path in to_upload:
        print(f"Uploading {file_path.name}:")
        upload_options["Filename"] = str(file_path.resolve())
        upload_options["Key"] = file_path.name
        upload_options["Callback"] = ProgressPercentage(
            file_path.stat().st_size, PROGRESS_BAR_WIDTH
        )
        try:
            client.upload_file(**upload_options)
        except S3UploadFailedError as e:
            sys.exit(e)

    print("Done.")


def get_object(get_client, args):
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


def delete_object(get_client, args):
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
