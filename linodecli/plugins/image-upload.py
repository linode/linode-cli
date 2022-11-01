"""
This plugin allows easy uploading of new Images to Linode's Images system.

Usage:

   linode-cli image-upload --region us-east --label my-image /path/to/image.gz
"""

import argparse
import os
from sys import exit

import requests

PLUGIN_BASE = "linode-cli image-upload"
MAX_UPLOAD_SIZE = 5 * 1024 * 1024 * 1024  # 5GB


def _progress(cur, total):
    """
    Draws the upload progress bar.
    """
    percent = "{:.1f}".format(100 * (cur / float(total)))
    progress = int(100 * cur // total)
    bar = ("#" * progress) + ("-" * (100 - progress))
    print("\r |{}| {}%".format(bar, percent), end="", flush=True)


class UploadProgressHelper:
    """
    Handles streaming uploads with python's requests library while printing a
    progress bar.
    """

    def __init__(self, filepath, chunk_size=5242880):
        self.filepath = filepath
        self.chunk_size = chunk_size
        self.read_size = 0
        self.total_size = os.path.getsize(filepath)

    def __iter__(self):
        """
        This is called by requests to get one chunk of data to upload.  Uploads
        are streamed from disk in chunks of the given size.  This will also update
        the progress bar.
        """
        with open(self.filepath, "rb") as upload_file:
            while True:
                data = upload_file.read(self.chunk_size)
                if not data:
                    _progress(self.total_size, self.total_size)
                    break
                self.read_size += len(data)
                _progress(self.read_size, self.total_size)
                yield data

    def __len__(self):
        return self.total_size


def call(args, context):
    """
    The entrypoint for this plugin
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE, add_help=True)

    parser.add_argument(
        "--region",
        metavar="REGION",
        nargs="?",
        help="The region to upload the image to.  The uploaded "
        "image will be available to deploy in all regions, "
        "but initial deploys will be faster in the same region. "
        "Uploads will be faster to regions closer to you. "
        "Your default configured region is used if this is "
        "omitted.",
    )
    parser.add_argument(
        "--label",
        metavar="LABEL",
        nargs="?",
        help="Label for the new Image.  If omitted, the filename " "will be used.",
    )
    parser.add_argument(
        "--description",
        metavar="DESC",
        nargs="?",
        help="A description for this Image.  Blank if omitted.",
    )
    parser.add_argument(
        "file",
        metavar="FILE",
        help="The image file to upload.  Should be a raw disk image "
        "compressed with gzip, in .img.gz format.  We recommend "
        "using unpartitioned images with an ext3 or ext4 filesystem.",
    )

    parsed = parser.parse_args(args)

    # get default region populated
    context.client.config.update(parsed, ["region"])

    # make sure the file exists and is ready to upload
    filepath = os.path.expanduser(parsed.file)

    if not os.path.isfile(filepath):
        print("No file at {}; must be a path to a valid file.".format(filepath))
        exit(2)

    # make sure it's not larger than the max upload size
    if os.path.getsize(filepath) > MAX_UPLOAD_SIZE:
        print(
            "File {} is too large; compressed size must be less than 5GB".format(
                filepath
            )
        )
        exit(2)

    if not parsed.region:
        print("No region provided.  Please set a default region or use --region")
        exit(1)

    label = parsed.label or os.path.basename(filepath)

    # generate an upload URL
    call_args = ["--region", parsed.region, "--label", label]
    if parsed.description:
        call_args += ["--description", parsed.description]

    status, resp = context.client.call_operation("images", "upload", call_args)

    if status != 200:
        if status == 401:
            print(
                "Your token was not authorized to use this endpoint.  Please "
                "reconfigure the CLI with `linode-cli configure` to ensure you "
                "can make this request."
            )
            exit(3)
        if status == 404:
            print(
                "It looks like you are not in the Machine Images Beta, and therefore "
                "cannot upload images yet.  Please stay tuned, or open a support ticket "
                "to request access."
            )
            exit(4)
        print("Upload failed with status {}; response was {}".format(status, resp))
        exit(3)

    # grab the upload URL and image data
    image = resp["image"]
    upload_url = resp["upload_to"]

    # attempt to do the upload - use a streaming upload so that large files won't
    # be loaded entirely into memory
    requests.put(
        upload_url,
        headers={
            "Content-type": "application/octet-stream",
        },
        data=UploadProgressHelper(filepath),
    )
    print()

    # supposing it all worked, show the new Image
    context.client.handle_command("images", "view", [str(image["id"])])
