"""
The static website module of CLI Plugin for handling object storage
"""

from argparse import ArgumentParser

from linodecli.plugins import inherit_plugin_args
from linodecli.plugins.obj.config import BASE_WEBSITE_TEMPLATE, PLUGIN_BASE


def enable_static_site(
    get_client, args, **kwargs
):  # pylint: disable=unused-argument
    """
    Turns a bucket into a static website
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " ws-create"))

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket to turn into a static site",
    )
    parser.add_argument(
        "--ws-index",
        metavar="INDEX",
        required=True,
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
    bucket = parsed.bucket

    # make the site
    print(f"Setting bucket {bucket} access control to be 'public-read'")

    client.put_bucket_acl(
        Bucket=bucket,
        ACL="public-read",
    )

    index_page = parsed.ws_index

    ws_config = {"IndexDocument": {"Suffix": index_page}}
    if parsed.ws_error:
        ws_config["ErrorDocument"] = {"Key": parsed.ws_error}

    client.put_bucket_website(
        Bucket=bucket,
        WebsiteConfiguration=ws_config,
    )

    print(
        "Static site now available at "
        f"{BASE_WEBSITE_TEMPLATE.format(cluster=client.cluster, bucket=bucket)}"
        "\nIf you still can't access the website, please check the "
        "Access Control List setting of the website related objects (files) "
        "in your bucket."
    )


def static_site_info(
    get_client, args, **kwargs
):  # pylint: disable=unused-argument
    """
    Returns info about a configured static site
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " ws-info"))

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket to return static site information on.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    bucket = parsed.bucket

    response = client.get_bucket_website(Bucket=bucket)

    index = response.get("IndexDocument", {}).get("Suffix", "Not Configured")
    error = response.get("ErrorDocument", {}).get("Key", "Not Configured")

    endpoint = BASE_WEBSITE_TEMPLATE.format(
        cluster=client.cluster, bucket=bucket
    )

    print(f"Bucket {bucket}: Website configuration")
    print(f"Website endpoint: {endpoint}")
    print(f"Index document: {index}")
    print(f"Error document: {error}")


def disable_static_site(
    get_client, args, **kwargs
):  # pylint: disable=unused-argument
    """
    Disables static site for a bucket
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " du"))

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        nargs="?",
        help="The bucket to disable static site for.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    bucket = parsed.bucket

    client.delete_bucket_website(Bucket=bucket)

    print(f"Website configuration deleted for {parsed.bucket}")
