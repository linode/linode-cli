# pylint: disable=too-many-lines
"""
CLI Plugin for handling OBJ
"""
import sys
from argparse import ArgumentParser

from linodecli.plugins import inherit_plugin_args
from linodecli.plugins.obj.config import PLUGIN_BASE

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


def set_acl(get_client, args):
    """
    Modify Access Control List for a Bucket or Objects
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " setacl"))

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
        "--acl-private",
        action="store_true",
        help="If given, makes the target private.",
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
    acl = "public-read" if parsed.acl_public else "private"
    bucket = parsed.bucket

    key = parsed.file
    set_acl_options = {
        "Bucket": bucket,
        "ACL": acl,
    }
    if key:
        set_acl_options["Key"] = key
        set_acl_func = client.put_object_acl
    else:
        set_acl_func = client.put_bucket_acl

    try:
        set_acl_func(**set_acl_options)
    except ClientError as e:
        sys.exit(e)
    print("ACL updated")
