import argparse
import getpass
import math
import os
import socket
import sys
import time
from datetime import datetime
from math import ceil

from terminaltables import SingleTable

ENV_ACCESS_KEY_NAME = "LINODE_CLI_OBJ_ACCESS_KEY"
ENV_SECRET_KEY_NAME = "LINODE_CLI_OBJ_SECRET_KEY"

try:
    import boto
    from boto.exception import BotoClientError, S3CreateError, S3ResponseError
    from boto.s3.connection import OrdinaryCallingFormat
    from boto.s3.key import Key
    from boto.s3.prefix import Prefix

    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


# replace {} with the cluster name
BASE_URL_TEMPLATE = "{}.linodeobjects.com"
BASE_WEBSITE_TEMPLATE = "website-{}.linodeobjects.com"

# for all date output
DATE_FORMAT = "%Y-%m-%d %H:%M"
INCOMING_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# for help commands
PLUGIN_BASE = "linode-cli obj"

# constant error messages
NO_SCOPES_ERROR = """Your OAuth token isn't authorized to create Object Storage keys.
To fix this, please generate a new token at this URL:

  https://cloud.linode.com/profile/tokens

Be sure to select 'Read/Write' for Object Storage and 'Read Only'
for Account during token generation (as well as any other access
you want the Linode CLI to have).

Once you've generated a new token, you can use it with the
Linode CLI by running this command and entering it:

  linode-cli configure
"""

NO_ACCESS_ERROR = """You are not authorized to use Object Storage at this time.
Please contact your Linode Account administrator to request
access, or ask them to generate Object Storage Keys for you."""


# Files larger than this need to be uploaded via a multipart upload
UPLOAD_MAX_FILE_SIZE = 1024 * 1024 * 1024 * 5
# This is how big (in MB) the chunks of the file that we upload will be
MULTIPART_UPLOAD_CHUNK_SIZE_DEFAULT = 1024

def restricted_int_arg_type(max, min=1):
    """
    An ArgumentParser arg type for integers that restricts the value to between `min` and `max`
    (inclusive for both.)
    """
    def restricted_int(string):
        err_msg = "Value must be an integer between {} and {}".format(min, max)
        try:
            value = int(string)
        except ValueError:
            # argparse can handle ValueErrors, but shows an unfriendly "invalid restricted_int
            # value: '0.1'" message, so catch and raise with a better message.
            raise argparse.ArgumentTypeError(err_msg)
        if value < min or value > max:
            raise argparse.ArgumentTypeError(err_msg)
        return value
    return restricted_int



def list_objects_or_buckets(get_client, args):
    """
    Lists buckets or objects
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " ls")

    parser.add_argument(
        "bucket",
        metavar="NAME",
        type=str,
        nargs="?",
        help="Optional.  If not given, lists all buckets.  If given, "
        "lists the contents of the given bucket.  May contain a "
        "/ followed by a directory path to show the contents of "
        "a directory within the named bucket.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    if parsed.bucket:
        # list objects
        if "/" in parsed.bucket:
            bucket_name, prefix = parsed.bucket.split("/", 1)
        else:
            bucket_name = parsed.bucket
            prefix = ""

        try:
            bucket = client.get_bucket(bucket_name)
        except S3ResponseError:
            print("No bucket named " + bucket_name)
            sys.exit(2)

        data = []
        for c in bucket.list(prefix=prefix, delimiter="/"):
            if isinstance(c, Prefix):
                size = "DIR"
            else:
                size = c.size

            datetime = _convert_datetime(c.last_modified) if size != "DIR" else " " * 16

            data.append([datetime, size, c.name])

        if data:
            tab = _borderless_table(data)
            print(tab.table)

        sys.exit(0)
    else:
        # list buckets
        buckets = client.get_all_buckets()

        data = [[_convert_datetime(b.creation_date), b.name] for b in buckets]

        tab = _borderless_table(data)
        print(tab.table)

        sys.exit(0)


def create_bucket(get_client, args):
    """
    Creates a new bucket
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " mb")

    parser.add_argument(
        "name", metavar="NAME", type=str, help="The name of the bucket to create."
    )

    parsed = parser.parse_args(args)
    client = get_client()

    client.create_bucket(parsed.name)

    print("Bucket {} created".format(parsed.name))
    sys.exit(0)


def delete_bucket(get_client, args):
    """
    Deletes a bucket
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " rb")

    parser.add_argument(
        "name", metavar="NAME", type=str, help="The name of the bucket to remove."
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="If given, force removal of non-empty buckets by deleting "
        "all objects in the bucket before deleting the bucket.  For "
        "large buckets, this may take a while.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    if parsed.recursive:
        try:
            bucket = client.get_bucket(parsed.name)
        except S3ResponseError:
            print("No bucket named " + parsed.name)
            sys.exit(2)

        for c in bucket.list():
            print("delete: {} {}".format(parsed.name, c.key))
            bucket.delete_key(c)

    client.delete_bucket(parsed.name)

    print("Bucket {} removed".format(parsed.name))

    sys.exit(0)


def upload_object(get_client, args):
    """
    Uploads an object to object storage
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " put")

    parser.add_argument(
        "file", metavar="FILE", type=str, nargs="+", help="The files to upload."
    )
    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket to put a file in."
    )
    parser.add_argument(
        "--acl-public",
        action="store_true",
        help="If set, the new object can be downloaded without " "authentication.",
    )
    parser.add_argument(
        "--chunk-size",
        type=restricted_int_arg_type(5120),
        default=MULTIPART_UPLOAD_CHUNK_SIZE_DEFAULT,
        help="The size of file chunks when uploading large files, in MB."
    )
    # parser.add_argument('--recursive', action='store_true',
    #                    help="If set, upload directories recursively.")

    parsed = parser.parse_args(args)
    client = get_client()

    to_upload = []
    to_multipart_upload = []
    for c in parsed.file:
        # find the object
        file_path = os.path.expanduser(c)

        if not os.path.isfile(file_path):
            print("No file {}".format(file_path))
            sys.exit(5)

        filename = os.path.split(file_path)[-1]

        file_size = os.path.getsize(file_path)

        if file_size >= UPLOAD_MAX_FILE_SIZE:
            to_multipart_upload.append((filename, file_path, file_size))
        else:
            to_upload.append((filename, file_path))

    # upload the files
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print("No bucket named " + parsed.bucket)
        sys.exit(2)

    policy = "public-read" if parsed.acl_public else None
    chunk_size = 1024 * 1024 * parsed.chunk_size

    for filename, file_path in to_upload:
        k = Key(bucket)
        k.key = filename

        print(filename)
        k.set_contents_from_filename(file_path, cb=_progress, num_cb=100, policy=policy)

    for filename, file_path, file_size in to_multipart_upload:
        _do_multipart_upload(bucket, filename, file_path, file_size, policy, chunk_size)

    print("Done.")


def _do_multipart_upload(bucket, filename, file_path, file_size, policy, chunk_size):
    """
    Handles the internals of a multipart upload for a large file.

    :param bucket: The bucket to upload the large file to
    :type bucket: Boto bucket
    :param filename: The name of the file to upload
    :type filename: str
    :param: file_path: That absolute path to the file we're uploading
    :type file_path: str
    :param file_size: The size of this file in bytes (used for chunking)
    :type file_size: int
    :param policy: The canned ACLs to include with the new key once the upload
                   completes.  None for no ACLs, or "public-read" to make the
                   key accessible publicly.
    :type policy: str
    :param chunk_size: The size of chunks to upload, in bytes.
    :type chunk_size: int
    """
    upload = bucket.initiate_multipart_upload(filename, policy=policy)

    # convert chunk_size to float so that division works like we want
    num_chunks = int(math.ceil(file_size / float(chunk_size)))

    print("{} ({} parts)".format(filename, num_chunks))

    num_tries = 3
    retry_delay = 2

    try:
        with open(file_path, "rb") as f:
            for i in range(num_chunks):
                print(" Part {}".format(i + 1))
                for attempt in range(num_tries):
                    try:
                        upload.upload_part_from_file(
                            f, i + 1, cb=_progress, num_cb=100, size=chunk_size
                        )
                    except S3ResponseError:
                        if attempt < num_tries - 1:
                            print( "  Part failed ({} of {} attempts). Retrying in {} seconds...".format(attempt + 1, num_tries, retry_delay))
                            time.sleep(retry_delay)
                            continue
                        else:
                            raise
                    else:
                        break
    except Exception:
        print("Upload failed!  Cleaning up!")
        upload.cancel_upload()
        raise

    upload.complete_upload()


def get_object(get_client, args):
    """
    Retrieves an uploaded object and writes it to a file
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " get")

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

    # download the file
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print("No bucket named " + parsed.bucket)
        sys.exit(2)

    k = bucket.get_key(parsed.file)

    if k is None:
        print("No {} in {}".format(parsed.file, parsed.bucket))
        sys.exit(2)

    k.get_contents_to_filename(destination, cb=_progress, num_cb=100)

    print("Done.")


def delete_object(get_client, args):
    """
    Removes a file from a bucket
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " del")

    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket to delete from."
    )
    parser.add_argument(
        "file", metavar="OBJECT", type=str, help="The object to remove."
    )

    parsed = parser.parse_args(args)
    client = get_client()

    # get the key to delete
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print("No bucket named " + parsed.bucket)
        sys.exit(2)

    k = bucket.get_key(parsed.file)

    if k is None:
        print("No {} in {}".format(parsed.file, parsed.bucket))
        sys.exit(2)

    # delete the key
    k.delete()

    print("{} removed from {}".format(parsed.file, parsed.bucket))


def generate_url(get_client, args):
    """
    Generates a URL to an object
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " signurl")

    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket containing the object."
    )
    parser.add_argument(
        "file", metavar="OBJECT", type=str, help="The object to sign a URL to."
    )
    parser.add_argument(
        "expiry",
        metavar="EXPIRY",
        type=str,
        help="When this link should expire.  Treated as an epoch "
        "time if a number. If starts with a '+' treated as "
        "an offset.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    now = datetime.now()

    if parsed.expiry.startswith("+"):
        # this is an offset in seconds
        offset = int(parsed.expiry[1:])
    else:
        expiry = int(parsed.expiry)
        offset = expiry - ceil(now.timestamp())

    # get the key
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print("No bucket named " + parsed.bucket)
        sys.exit(2)

    k = bucket.get_key(parsed.file)

    if k is None:
        print("No {} in {}".format(parsed.file, parsed.bucket))
        sys.exit(2)

    url = k.generate_url(offset)

    print(url)


def set_acl(get_client, args):
    """
    Modify Access Control List for a Bucket or Objects
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " setacl")

    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket to modify."
    )
    parser.add_argument(
        "file",
        metavar="OBJECT",
        type=str,
        nargs="?",
        help="Optional.  The object to modify.  If omitted, modifies "
        "the ACLs for the entire bucket.",
    )
    parser.add_argument(
        "--acl-public",
        action="store_true",
        help="If given, makes the target publicly readable.",
    )
    parser.add_argument(
        "--acl-private", action="store_true", help="If given, makes the target private."
    )

    parsed = parser.parse_args(args)
    client = get_client()

    # make sure the call is sane
    if parsed.acl_public and parsed.acl_private:
        print("You may not set the ACL to public and private in the same call")
        sys.exit(1)

    if not parsed.acl_public and not parsed.acl_private:
        print("You must choose an ACL to apply")
        sys.exit(1)

    # get the bucket
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print("No bucket named " + parsed.bucket)
        sys.exit(2)

    act_on = bucket

    if parsed.file:
        k = bucket.get_key(parsed.file)

        if k is None:
            print("No {} in {}".format(parsed.file, parsed.bucket))
            sys.exit(2)

        act_on = k

    act_on.set_acl("public-read" if parsed.acl_public else "private")
    print("ACL updated")


def enable_static_site(get_client, args):
    """
    Turns a bucket into a static website
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " ws-create")

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket to turn into a static site",
    )
    parser.add_argument(
        "--ws-index",
        metavar="INDEX",
        type=str,
        help="The file to serve as the index of the website",
    )
    parser.add_argument(
        "--ws-error",
        metavar="ERROR",
        type=str,
        help="The file to serve as the error page of the website",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    # get the bucket
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print("No bucket named " + parsed.bucket)
        sys.exit(2)

    # make the site
    bucket.set_acl("public-read")
    bucket.configure_website(parsed.ws_index, parsed.ws_error)
    print(
        "Static site now available at https://{}.website-{}.linodeobjects.com".format(
            parsed.bucket, client.obj_cluster
        )
    )


def static_site_info(get_client, args):
    """
    Returns info about a configured static site
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " ws-info")

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket to return static site information on.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    # get the bucket
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print("No bucket named " + parsed.bucket)
        sys.exit(2)

    info = bucket.get_website_configuration()

    index = info["WebsiteConfiguration"]["IndexDocument"]["Suffix"]
    error = info["WebsiteConfiguration"]["ErrorDocument"]["Key"]

    print("Bucket {}: Website configuration".format(parsed.bucket))
    print(
        "Website endpoint: {}.{}".format(
            parsed.bucket, BASE_WEBSITE_TEMPLATE.format(client.host.split(".")[0])
        )
    )
    print("Index document: {}".format(index))
    print("Error document: {}".format(error))


def show_usage(get_client, args):
    """
    Shows space used by all buckets in this cluster, and total space
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " du")

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        nargs="?",
        help="Optional.  If given, only shows usage for that bucket. "
        "If omitted, shows usage for all buckets.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    if parsed.bucket:
        try:
            buckets = [client.get_bucket(parsed.bucket)]
        except S3ResponseError:
            print("No bucket named " + parsed.bucket)
            sys.exit(2)
    else:
        # all buckets
        buckets = client.get_all_buckets()

    grand_total = 0
    for b in buckets:
        # find total size of each
        total = num = 0
        for obj in b.list():
            num += 1
            total += obj.size

        grand_total += total

        total = _denominate(total)

        tab = _borderless_table(
            [[_pad_to(total, length=7), "{} objects".format(num), b.name]]
        )
        print(tab.table)

    if len(buckets) > 1:
        print("--------")
        print("{} Total".format(_denominate(grand_total)))

    exit(0)


def _denominate(total):
    """
    Coverts bucket size to human readable bytes.
    """
    total = float(total)
    denomination = ["KB", "MB", "GB", "TB"]
    for x in denomination:
        if total > 1024:
            total = total / 1024
        if total < 1024:
            total = round(total, 2)
            total = str(total) + " " + x
            break
    return total


def list_all_objects(get_client, args):
    """
    Lists all objects in all buckets
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " la")
    parsed = parser.parse_args(args)
    client = get_client()

    # all buckets
    buckets = client.get_all_buckets()

    for b in buckets:
        print()

        for obj in b.list():
            if isinstance(obj, Prefix):
                size = "DIR"
            else:
                size = obj.size

            print(
                "{} {}   {}/{}".format(
                    _convert_datetime(obj.last_modified) if size != "DIR" else " " * 16,
                    _pad_to(size, 9, right_align=True),
                    b.name,
                    obj.key,
                )
            )

    exit(0)


def disable_static_site(get_client, args):
    """
    Disables static site for a bucket
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE + " du")

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        nargs="?",
        help="The bucket to disable static site for.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    # get the bucket
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print("No bucket named " + parsed.bucket)
        sys.exit(2)

    # make the site
    bucket.delete_website_configuration()
    print("Website configuration deleted for {}".format(parsed.bucket))


COMMAND_MAP = {
    "mb": create_bucket,
    "rb": delete_bucket,
    "ls": list_objects_or_buckets,
    "la": list_all_objects,
    "du": show_usage,
    "put": upload_object,
    "get": get_object,
    "rm": delete_object,
    "del": delete_object,
    #'sync': sync_dir, TODO - syncs a directory
    "signurl": generate_url,
    "setacl": set_acl,
    "ws-create": enable_static_site,
    "ws-info": static_site_info,
    "ws-delete": disable_static_site,
    #'info': get_info,
}


def call(args, context):
    """
    This is called when the plugin is invoked
    """
    if not HAS_BOTO:
        # we can't do anything - ask for an install
        pip_version = "pip3" if sys.version[0] == 3 else "pip"

        print(
            "This plugin requires the 'boto' module.  Please install it by running "
            "'{} install boto'".format(pip_version)
        )

        sys.exit(2)  # requirements not met - we can't go on

    parser = argparse.ArgumentParser(PLUGIN_BASE, add_help=False)
    parser.add_argument(
        "command",
        metavar="COMMAND",
        nargs="?",
        type=str,
        help="The command to execute in object storage",
    )
    parser.add_argument(
        "--cluster",
        metavar="CLUSTER",
        type=str,
        help="The cluster to use for the operation",
    )

    parsed, args = parser.parse_known_args(args)

    # don't mind --no-defaults if it's there; the top-level parser already took care of it
    try:
        args.remove("--no-defaults")
    except ValueError:
        pass

    if not parsed.command:
        # show help if invoked with no command
        parser.print_help()

        # additional help
        print()
        print("Available commands: ")

        command_help_map = [
            [name, func.__doc__.strip()] for name, func in sorted(COMMAND_MAP.items())
        ]

        tab = SingleTable(command_help_map)
        tab.inner_heading_row_border = False
        print(tab.table)
        print()
        print(
            "Additionally, you can regenerate your Object Storage keys using the "
            "'regenerate-keys' command or configure defaults for the plugin using "
            "the 'configure' command."
        )
        print()
        print("See --help for individual commands for more information")

        exit(0)

    # make a client, but only if we weren't printing help

    access_key, secret_key = (
        os.environ.get(ENV_ACCESS_KEY_NAME, None),
        os.environ.get(ENV_SECRET_KEY_NAME, None),
    )

    if not "--help" in args:
        if access_key and not secret_key or secret_key and not access_key:
            print(
                "You must set both {} and {}, or neither".format(
                    ENV_ACCESS_KEY_NAME, ENV_SECRET_KEY_NAME
                )
            )
            exit(1)

        # not given on command line, so look them up
        if not access_key:
            access_key, secret_key = _get_s3_creds(context.client)

    cluster = parsed.cluster
    if context.client.defaults:
        cluster = cluster or context.client.config.plugin_get_value("cluster")

    def get_client():
        """
        Get the boto client based on the cluster, or ask to configure a default cluster if one is not specified.
        This is in a method so command methods can do this work AFTER displaying help, that way help can be shown
        without specifying a cluster or having a valid OBJ key.
        """
        current_cluster = cluster
        if current_cluster is None and not context.client.defaults:
            print("Error: cluster is required.")
            exit(1)

        if current_cluster is None:
            print(
                "Error: No default cluster is configured.  Either configure the CLI "
                "or invoke with --cluster to specify a cluster."
            )
            _configure_plugin(context.client)
            current_cluster = context.client.config.plugin_get_value("cluster")

        return _get_boto_client(current_cluster, access_key, secret_key)

    if parsed.command in COMMAND_MAP:
        try:
            COMMAND_MAP[parsed.command](get_client, args)
        except S3ResponseError as e:
            if e.error_code:
                print("Error: {}".format(e.error_code))
            else:
                print(e)
            sys.exit(4)
        except S3CreateError as e:
            print("Error: {}".format(e))
            sys.exit(5)
        except BotoClientError as e:
            message_parts = e.message.split(":")
            if len(message_parts) > 0:
                message = ":".join(message_parts[0:])
            else:
                message = e.message
            print("Error: {}".format(message))
            sys.exit(6)
    elif parsed.command == "regenerate-keys":
        print("Regenerating Object Storage keys..")
        _get_s3_creds(context.client, force=True)
        print("Done.")
        print(
            "Warning: Your old Object Storage keys _were not_ automatically expired!  If you want "
            "to expire them, see `linode-cli object-storage keys-list` and "
            "`linode-cli object-storage keys-delete [KEYID]`."
        )
    elif parsed.command == "configure":
        _configure_plugin(context.client)
    else:
        print("No command {}".format(parsed.command))
        sys.exit(1)


def _get_boto_client(cluster, access_key, secret_key):
    """
    Returns a boto client object that can be used to communicate with the Object
    Storage cluster.
    """
    client = boto.connect_s3(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        host=BASE_URL_TEMPLATE.format(cluster),
        calling_format=OrdinaryCallingFormat(),
    )

    # set this for later use
    client.obj_cluster = cluster

    return client


def _get_s3_creds(client, force=False):
    """
    Retrieves stored s3 creds for the acting user from the config, or generates new
    creds using the client and stores them if none exist

    :param client: The client object from the invoking PluginContext
    :type client: linodecli.CLI
    :param force: If True, get new creds even if there are already creds stored.
                  This is used to rotate creds.
    :type force: bool

    :returns: The access key and secret key for this user
    :rtype: tuple(str, str)
    """
    access_key = client.config.plugin_get_value("access-key")
    secret_key = client.config.plugin_get_value("secret-key")

    if force or access_key is None:
        # this means there are no stored s3 creds for this user - set them up

        # but first - is there actually a config?  If we got this far, creds aren't
        # being provided by the environment, but if the CLI is running without a
        # config, we shouldn't generate new keys (or we'd end up doing so with each
        # request) - instead ask for them to be set up.
        if client.config.get_value("token") is None:
            print(
                "You are running the Linode CLI without a configuration file, but "
                "object storage keys were not configured.  Please set the following "
                "variables in your environment: '{}' and '{}'.  If you'd rather ".format(
                    ENV_ACCESS_KEY_NAME, ENV_SECRET_KEY_NAME
                )
                + "configure the CLI, unset the 'LINODE_CLI_TOKEN' environment "
                "variable and then run `linode-cli configure`."
            )
            exit(1)

        # before we do anything, can they do object storage?
        status, resp = client.call_operation("account", "view")

        if status != 200:
            if status == 401:
                # special case - oauth token isn't allowed to do this
                print(NO_SCOPES_ERROR)
                sys.exit(4)
            if status == 403:
                # special case - restricted users can't use obj
                print(NO_ACCESS_ERROR)
                sys.exit(4)
            # something went wrong - give up
            print("Key generation failed!")
            sys.exit(4)

        # label caps at 50 characters - trim some stuff maybe
        # static characters in label account for 13 total
        # timestamp is 10 more
        # allow 13 characters both for username and hostname
        timestamp_part = str(time.time()).split(".")[0]
        truncated_user = getpass.getuser()[:13]
        truncated_hostname = socket.gethostname()[:13]

        creds_label = "linode-cli-{}@{}-{}".format(
            truncated_user, truncated_hostname, timestamp_part
        )

        if len(creds_label) > 50:
            # if this is somehow still too long, trim from the front
            creds_label = creds_label[50 - len(creds_label) :]

        status, resp = client.call_operation(
            "object-storage", "keys-create", ["--label", "{}".format(creds_label)]
        )

        if status != 200:
            if status == 401:
                # special case - oauth token isn't allowed to do this
                print(NO_SCOPES_ERROR)
                sys.exit(4)
            if status == 403:
                # special case - restricted users can't use obj
                print(NO_ACCESS_ERROR)
                sys.exit(4)
            # something went wrong - give up
            print("Key generation failed!")
            sys.exit(3)

        access_key = resp["access_key"]
        secret_key = resp["secret_key"]

        client.config.plugin_set_value("access-key", access_key)
        client.config.plugin_set_value("secret-key", secret_key)
        client.config.write_config(silent=True)

    return access_key, secret_key


def _configure_plugin(client):
    """
    Configures a default cluster value.
    """
    clusters = [
        c["id"]
        for c in client.config._do_get_request(
            "/object-storage/clusters", token=client.config.get_value("token")
        )["data"]
    ]

    cluster = client.config._default_thing_input(
        "Configure a default Cluster for operations.",
        clusters,
        "Default Cluster: ",
        "Please select a valid Cluster",
        optional=False,  # this is the only configuration right now
    )

    client.config.plugin_set_value("cluster", cluster)
    client.config.write_config()


def _progress(cur, total):
    """
    Draws the upload progress bar.
    """
    percent = ("{:.1f}").format(100 * (cur / float(total)))
    progress = int(100 * cur // total)
    bar = ("#" * progress) + ("-" * (100 - progress))
    print("\r |{}| {}%".format(bar, percent), end="\r")

    if cur == total:
        print()


# helper functions for output
def _borderless_table(data):
    """
    Returns a terminaltables.SingleTable object with no borders and correct padding
    """
    tab = SingleTable(data)
    tab.inner_heading_row_border = False
    tab.inner_column_border = False
    tab.outer_border = False
    tab.padding_left = 0
    tab.padding_right = 2

    return tab


def _convert_datetime(datetime_str):
    """
    Given a string in INCOMING_DATE_FORMAT, returns a string in DATE_FORMAT
    """
    return datetime.strptime(datetime_str, INCOMING_DATE_FORMAT).strftime(DATE_FORMAT)


def _pad_to(val, length=10, right_align=False):
    """
    Pads val to be at minimum length characters long
    """
    ret = str(val)
    padding = ""

    if len(ret) < 10:
        padding = " " * (10 - len(ret))

    if right_align:
        ret = padding + ret
    else:
        ret = ret + padding

    return ret
