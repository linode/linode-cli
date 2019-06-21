from __future__ import print_function
import argparse
import base64
from datetime import datetime
import getpass
import socket
import sys
import time
import os
from subprocess import call as spcall, Popen, PIPE
import hashlib
import shutil
from terminaltables import SingleTable
from math import ceil
from linodecli.configuration import input_helper


try:
    import boto
    from boto.exception import S3CreateError, S3ResponseError, BotoClientError
    from boto.s3.connection import OrdinaryCallingFormat
    from boto.s3.key import Key
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


# replace {} with the cluster name
BASE_URL_TEMPLATE = '{}.linodeobjects.com'
BASE_WEBSITE_TEMPLATE = 'website-{}.linodeobjects.com'

# for all date output
DATE_FORMAT = '%Y-%m-%d %H:%M'
INCOMING_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

# for help commands
PLUGIN_BASE = 'linode-cli obj'


def list_objects_or_buckets(client, args):
    """
    Lists buckets or objects
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' ls')

    parser.add_argument('bucket', metavar='NAME', type=str, nargs='?',
                        help="Optional.  If not given, lists all buckets.  If given, "
                             "lists the contents of the given bucket.")

    parsed = parser.parse_args(args)

    if parsed.bucket:
        # list objects
        try:
            bucket = client.get_bucket(parsed.bucket)
        except S3ResponseError:
            print('No bucket named '+parsed.bucket)
            sys.exit(2)

        data = []
        for c in bucket.list():
            if c.key.count('/') > 1 or ('/' in c.key and not c.key.endswith('/')):
                continue

            size = c.size
            if size == 0:
                size = 'DIR'

            datetime = _convert_datetime(c.last_modified) if size != 'DIR' else ' '*16

            data.append([datetime, size, c.name])

        if data:
            tab = _borderless_table(data)
            print(tab.table)

        sys.exit(0)
    else:
        # list buckets
        buckets = client.get_all_buckets()

        data = [
                [_convert_datetime(b.creation_date), b.name] for b in buckets
        ]

        tab = _borderless_table(data)
        print(tab.table)

        sys.exit(0)


def create_bucket(client, args):
    """
    Creates a new bucket
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' mb')

    parser.add_argument('name', metavar='NAME', type=str,
                        help="The name of the bucket to create.")

    parsed = parser.parse_args(args)

    client.create_bucket(parsed.name)

    print('Bucket {} created'.format(parsed.name))
    sys.exit(0)


def delete_bucket(client, args):
    """
    Deletes a bucket
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' rb')

    parser.add_argument('name', metavar='NAME', type=str,
                        help="The name of the bucket to remove.")

    parsed = parser.parse_args(args)

    client.delete_bucket(parsed.name)

    print("Bucket {} removed".format(parsed.name))

    sys.exit(0)


def upload_object(client, args):
    """
    Uploads an object to object storage
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' put')

    parser.add_argument('file', metavar='FILE', type=str, nargs='+',
                        help="The files to upload.")
    parser.add_argument('bucket', metavar='BUCKET', type=str,
                        help="The bucket to put a file in.")
    parser.add_argument('--acl-public', action='store_true',
                        help="If set, the new object can be downloaded without "
                             "authentication.")
    #parser.add_argument('--recursive', action='store_true',
    #                    help="If set, upload directories recursively.")

    parsed = parser.parse_args(args)

    to_upload = []
    for c in parsed.file:
        # find the object
        file_path = os.path.expanduser(c)

        if not os.path.isfile(file_path):
            print('No file {}'.format(file_path))
            sys.exit(5)

        filename = os.path.split(file_path)[-1]

        to_upload.append((filename, file_path))

    # upload the files
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print('No bucket named '+parsed.bucket)
        sys.exit(2)

    for filename, file_path in to_upload:
        k = Key(bucket)
        k.key = filename

        print(filename)
        policy = 'public-read' if parsed.acl_public else None
        k.set_contents_from_filename(file_path, cb=_progress, num_cb=100, policy=policy)

    print('Done.')


def get_object(client, args):
    """
    Retrieves an uploaded object and writes it to a file
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' get')

    parser.add_argument('bucket', metavar='BUCKET', type=str,
                        help="The bucket the file is in.")
    parser.add_argument('file', metavar='OBJECT', type=str,
                        help="The object to retrieve.")
    parser.add_argument('destination', metavar='LOCAL_FILE', type=str, nargs='?',
                        help='The destination file. If omitted, uses the object '
                             'name and saves to the current directory.')

    parsed = parser.parse_args(args)

    # find destination file
    destination = parsed.destination

    if destination is None:
        destination = parsed.file

    # download the file
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print('No bucket named '+parsed.bucket)
        sys.exit(2)

    k = bucket.get_key(parsed.file)

    if k is None:
        print('No {} in {}'.format(parsed.file, parsed.bucket))
        sys.exit(2)

    k.get_contents_to_filename(destination, cb=_progress, num_cb=100)

    print('Done.')


def delete_object(client, args):
    """
    Removes a file from a bucket
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' del')

    parser.add_argument('bucket', metavar='BUCKET', type=str,
                        help="The bucket to delete from.")
    parser.add_argument('file', metavar='OBJECT', type=str,
                        help="The object to remove.")

    parsed = parser.parse_args(args)

    # get the key to delete
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print('No bucket named '+parsed.bucket)
        sys.exit(2)

    k = bucket.get_key(parsed.file)

    if k is None:
        print('No {} in {}'.format(parsed.file, parsed.bucket))
        sys.exit(2)

    # delete the key
    k.delete()

    print('{} removed from {}'.format(parsed.file, parsed.bucket))


def generate_url(client, args):
    """
    Generates a URL to an object
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' signurl')

    parser.add_argument('bucket', metavar='BUCKET', type=str,
                        help="The bucket containing the object.")
    parser.add_argument('file', metavar='OBJECT', type=str,
                        help="The object to sign a URL to.")
    parser.add_argument('expiry', metavar='EXPIRY', type=str,
                        help="When this link should expire.  Treated as an epoch "
                             "time if a number. If starts with a '+' treated as "
                             "an offset.")

    parsed = parser.parse_args(args)

    now = datetime.now()

    if parsed.expiry.startswith('+'):
        # this is an offset in seconds
        offset = int(parsed.expiry[1:])
    else:
        expiry = int(parsed.expiry)
        offset = expiry - ceil(now.timestamp())

    # get the key
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print('No bucket named '+parsed.bucket)
        sys.exit(2)

    k = bucket.get_key(parsed.file)

    if k is None:
        print('No {} in {}'.format(parsed.file, parsed.bucket))
        sys.exit(2)

    url = k.generate_url(offset)

    print(url)


def set_acl(client, args):
    """
    Modify Access Control List for a Bucket or Objects
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' setacl')

    parser.add_argument('bucket', metavar='BUCKET', type=str,
                        help="The bucket to modify.")
    parser.add_argument('file', metavar='OBJECT', type=str, nargs='?',
                        help="Optional.  The object to modify.  If omitted, modifies "
                             "the ACLs for the entire bucket.")
    parser.add_argument('--acl-public', action='store_true',
                        help="If given, makes the target publicly readable.")
    parser.add_argument('--acl-private', action='store_true',
                        help="If given, makes the target private.")

    parsed = parser.parse_args(args)

    # make sure the call is sane
    if parsed.acl_public and parsed.acl_private:
        print('You may not set the ACL to public and private in the same call')
        sys.exit(1)

    if not parsed.acl_public and not parsed.acl_private:
        print('You must choose an ACL to apply')
        sys.exit(1)

    # get the bucket
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print('No bucket named '+parsed.bucket)
        sys.exit(2)

    act_on = bucket

    if parsed.file:
        k = bucket.get_key(parsed.file)

        if k is None:
            print('No {} in {}'.format(parsed.file, parsed.bucket))
            sys.exit(2)

        act_on = k

    act_on.set_acl('public-read' if parsed.acl_public else 'private')
    print('ACL updated')


def enable_static_site(client, args):
    """
    Turns a bucket into a static website
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' ws-create')

    parser.add_argument('bucket', metavar='BUCKET', type=str,
                        help="The bucket to turn into a static site")
    parser.add_argument('--ws-index', metavar='INDEX', type=str,
                        help='The file to serve as the index of the website')
    parser.add_argument('--ws-error', metavar='ERROR', type=str,
                        help='The file to serve as the error page of the website')

    parsed = parser.parse_args(args)

    # get the bucket
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print('No bucket named '+parsed.bucket)
        sys.exit(2)

    # make the site
    bucket.set_acl('public-read')
    bucket.configure_website(parsed.ws_index, parsed.ws_error)
    print(
        'Static site now available at https://{}.website-{}.linodeobjects.com'.format(
            parsed.bucket, client.obj_cluster
    ))


def static_site_info(client, args):
    """
    Returns info about a configured static site
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' ws-info')

    parser.add_argument('bucket', metavar='BUCKET', type=str,
                        help="The bucket to return static site information on.")

    parsed = parser.parse_args(args)

    # get the bucket
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print('No bucket named '+parsed.bucket)
        sys.exit(2)

    info = bucket.get_website_configuration()

    index = info['WebsiteConfiguration']['IndexDocument']['Suffix']
    error = info['WebsiteConfiguration']['ErrorDocument']['Key']

    print('Bucket {}: Website configuration'.format(parsed.bucket))
    print('Website endpoint: {}.{}'.format(
            parsed.bucket,
            BASE_WEBSITE_TEMPLATE.format(client.host.split('.')[0])
    ))
    print('Index document: {}'.format(index))
    print('Error document: {}'.format(error))


def show_usage(client, args):
    """
    Shows space used by all buckets in this cluster, and total space
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' du')

    parser.add_argument('bucket', metavar='BUCKET', type=str, nargs='?',
                        help="Optional.  If given, only shows usage for that bucket. "
                             "If omitted, shows usage for all buckets.")

    parsed = parser.parse_args(args)

    if parsed.bucket:
        try:
            buckets = [client.get_bucket(parsed.bucket)]
        except S3ResponseError:
            print('No bucket named '+parsed.bucket)
            sys.exit(2)
    else:
        # all buckets
        buckets = client.get_all_buckets()

    grand_total = 0
    for b in buckets:
        # find total size of each
        total = num  = 0
        for obj in b.list():
            num += 1
            total += obj.size

        grand_total += total
        tab = _borderless_table([[_pad_to(total, length=7), '{} objects'.format(num), b.name]])
        print(tab.table)

    if len(buckets) > 1:
        print('--------')
        print('{} Total'.format(grand_total))

    exit(0)


def list_all_objects(client, args):
    """
    Lists all objects in all buckets
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' la')
    parsed = parser.parse_args(args)

    # all buckets
    buckets = client.get_all_buckets()

    for b in buckets:
        print()

        for obj in b.list():
            if obj.key.count('/') > 1 or ('/' in obj.key and not obj.key.endswith('/')):
                continue

            size = obj.size
            if size == 0:
                size = 'DIR'

            print('{} {}   {}/{}'.format(
                _convert_datetime(obj.last_modified) if size != 'DIR' else ' '*16,
                _pad_to(size, 9, right_align=True),
                b.name,
                obj.key
            ))

    exit(0)


def disable_static_site(client, args):
    """
    Disables static site for a bucket
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE+' du')

    parser.add_argument('bucket', metavar='BUCKET', type=str, nargs='?',
                        help="The bucket to disable static site for.")

    parsed = parser.parse_args(args)

    # get the bucket
    try:
        bucket = client.get_bucket(parsed.bucket)
    except S3ResponseError:
        print('No bucket named '+parsed.bucket)
        sys.exit(2)

    # make the site
    bucket.delete_website_configuration()
    print('Website configuration deleted for {}'.format(parsed.bucket))


COMMAND_MAP = {
    'mb': create_bucket,
    'rb': delete_bucket,
    'ls': list_objects_or_buckets,
    'la': list_all_objects,
    'du': show_usage,
    'put': upload_object,
    'get': get_object,
    'rm': delete_object,
    'del': delete_object,
    #'sync': sync_dir, TODO - syncs a directory
    'signurl': generate_url,
    'setacl': set_acl,
    'ws-create': enable_static_site,
    'ws-info': static_site_info,
    'ws-delete': disable_static_site,
    #'info': get_info,
}


def call(args, context):
    """
    This is called when the plugin is invoked
    """
    if not HAS_BOTO:
        # we can't do anything - ask for an install
        pip_version = 'pip3' if sys.version[0] == 3 else 'pip'

        print("This plugin requires the 'boto' module.  Please install it by running "
              "'{} install boto'".format(pip_version))

        sys.exit(2) # requirements not met - we can't go on

    access_key, secret_key = _get_s3_creds(context.client)

    parser = argparse.ArgumentParser(PLUGIN_BASE, add_help=False)
    parser.add_argument('command', metavar='COMMAND', nargs='?', type=str,
                        help='The command to execute in object storage')
    parser.add_argument('--cluster', metavar='CLUSTER', type=str,
                        help='The cluster to use.  Defaults to us-east-1 (presently)')

    parsed, args = parser.parse_known_args(args)

    client = _get_boto_client(parsed.cluster or 'us-east-1', access_key, secret_key)

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
        tab.inner_heading_row_border=False
        print(tab.table)
        print()
        print('See --help for individual commands for more information')

        exit(0)

    if parsed.command in COMMAND_MAP:
        try:
            COMMAND_MAP[parsed.command](client, args)
        except S3ResponseError as e:
            if e.error_code:
                print('Error: {}'.format(e.error_code))
            else:
                print(e)
            sys.exit(4)
        except S3CreateError as e:
            print('Error: {}'.format(e))
            sys.exit(5)
        except BotoClientError as e:
            message_parts = e.message.split(':')
            if len(message_parts) > 0:
                message = ':'.join(message_parts[0:])
            else:
                message = e.message
            print('Error: {}'.format(message))
            sys.exit(6)
    else:
        print('No command {}'.format(parsed.command))
        sys.exit(1)


def _get_boto_client(cluster, access_key, secret_key):
    """
    Returns a boto client object that can be used to communicate with the Object
    Storage cluster.
    """
    client = boto.connect_s3(aws_access_key_id=access_key,
                             aws_secret_access_key=secret_key,
                             host=BASE_URL_TEMPLATE.format(cluster),
                             calling_format=OrdinaryCallingFormat())

    # set this for later use
    client.obj_cluster = cluster

    return client


def _get_s3_creds(client):
    """
    Retrieves stored s3 creds for the acting user from the config, or generates new
    creds using the client and stores them if none exist

    :param client: The client object from the invoking PluginContext
    :type client: linodecli.CLI

    :returns: The access key and secret key for this user
    :rtype: tuple(str, str)
    """
    access_key = client.config.plugin_get_value('access-key')
    secret_key = client.config.plugin_get_value('secret-key')

    if access_key is None:
        # this means there are no stored s3 creds for this user - set them up

        # before we do anything, can they do object storage?
        status, resp = client.call_operation('account', 'view')

        if status != 200:
            # something went wrong - give up
            print('Key generation failed!')
            sys.exit(4)

        if 'Object Storage' not in resp['capabilities']:
            # this account isn't in the EAP :( help them out
            print('You are not yet enrolled in the Object Storage Early Adopters Program.')
            result = input_helper('Would you like to request enrollment now? [Y/n]')

            if result in ('','y','Y'):
                status, resp = client.call_operation('tickets', 'create', [
                        '--summary', 'Looking to join Object Storage Early Adopters Program',
                        '--description', 'Please grant me access to the Object Storage Early '
                                         'Adopters Program.  This ticket generated by the Linode CLI.'
                ])
                
                if status != 200:
                    print('Ticket submission failed!  Please open a ticket requesting '
                          'access with `linode-cli tickets create`')
                    sys.exit(5)

                print('Ticket "Looking to join Object Storage Early Adopters Program" opened!')
                print("Please keep an eye on that ticket for updates, and try again once you're enrolled.")
            exit(0)

        # label caps at 50 characters - trim some stuff maybe
        # static characters in label account for 13 total
        # timestamp is 10 more
        # allow 13 characters both for username and hostname
        timestamp_part = str(time.time()).split('.')[0]
        truncated_user = getpass.getuser()[:13]
        truncated_hostname = socket.gethostname()[:13]

        creds_label = 'linode-cli-{}@{}-{}'.format(
                truncated_user,
                truncated_hostname,
                timestamp_part)

        if len(creds_label) > 50:
            # if this is somehow still too long, trim from the front
            creds_label = creds_label[50-len(creds_label):]

        status, resp = client.call_operation('object-storage', 'keys-create',
                                             ['--label', "{}".format(creds_label)])

        if status != 200:
            # something went wrong - give up
            print('Key generation failed!')
            sys.exit(3)

        access_key = resp['access_key']
        secret_key = resp['secret_key']

        client.config.plugin_set_value('access-key', access_key)
        client.config.plugin_set_value('secret-key', secret_key)
        client.config.write_config(silent=True)

    return access_key, secret_key


def _progress(cur, total):
    """
    Draws the upload progress bar.
    """
    percent = ("{0:.1f}").format(100 * (cur / float(total)))
    progress = int(100 * cur // total)
    bar = ('#' * progress) + ('-' * (100 - progress))
    print('\r |{}| {}%'.format(bar, percent), end='\r')

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
    tab.padding_left=0
    tab.padding_right=2

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
    if len(ret) < 10:
        padding = " "*(10-len(ret))

    if right_align:
        ret = padding + ret
    else:
        ret = ret + padding

    return ret
