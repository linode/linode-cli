"""
The config of the object storage plugin.
"""

import shutil

ENV_ACCESS_KEY_NAME = "LINODE_CLI_OBJ_ACCESS_KEY"
ENV_SECRET_KEY_NAME = "LINODE_CLI_OBJ_SECRET_KEY"
# replace {} with the cluster name
BASE_URL_TEMPLATE = "https://{}.linodeobjects.com"
BASE_WEBSITE_TEMPLATE = "{bucket}.website-{cluster}.linodeobjects.com"

# for all date output
DATE_FORMAT = "%Y-%m-%d %H:%M"
INCOMING_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# for help commands
PLUGIN_BASE = "linode-cli obj"

columns = shutil.get_terminal_size(fallback=(80, 24)).columns
PROGRESS_BAR_WIDTH = columns - 20 if columns > 30 else columns

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

NO_ACCESS_ERROR = (
    "You are not authorized to use Object Storage at this time.\n"
    "Please contact your Linode Account administrator to request\n"
    "access, or ask them to generate Object Storage Keys for you\n"
)


# Files larger than this need to be uploaded via a multipart upload
UPLOAD_MAX_FILE_SIZE = 1024 * 1024 * 1024 * 5
# This is how big (in MB) the chunks of the file that we upload will be
MULTIPART_UPLOAD_CHUNK_SIZE_DEFAULT = 1024
