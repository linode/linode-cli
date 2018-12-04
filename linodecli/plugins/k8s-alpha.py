"""
The alpha plugin includes Linode CLI features which are in an early,
pre-release, state.
"""
import argparse
import sys
import os
from subprocess import call as spcall
import hashlib
import shutil
from terminaltables import SingleTable

plugin_name = os.path.basename(__file__)[:-3]

def call(args, context):
    parser = argparse.ArgumentParser("{}".format(plugin_name), add_help=False)
    parser.add_argument('command', metavar='COMMAND', nargs='?', type=str,
                        help="The clusters command to be invoked.")
    parsed, args = parser.parse_known_args(args)

    commands = { 'create': create, 'delete': delete }
    
    if parsed.command is None or (parsed.command is None and parsed.help):
        parser.print_help()
        print_available_commands(commands)
        sys.exit(0)

    if parsed.command in commands.keys():
        commands[parsed.command](args, context)
    else:
        print('Unrecognized command {}'.format(parsed.command))

def create(args, context):
    parser = argparse.ArgumentParser("{} create".format(plugin_name), add_help=True)
    parser.add_argument('name', metavar='NAME', type=str,
                        help="A name for the cluster.")
#    parser.add_argument('--ha', metavar="MASTERS", type=int, required=False,
#                        choices=[3, 5],
#                        help="Make the cluster highly-available with MASTERS "
#                             "number of masters (3 or 5)")
    parsed = parser.parse_args(args)

    # Check if Terraform is installed
    try:
        nullf = open(os.devnull, 'w')
        spcall(['terraform'], stdout=nullf)
    except:
        print('To create a cluster you must first install Terraform\n'
              'https://learn.hashicorp.com/terraform/getting-started/install.html'
              '\n\nThis command will automatically download and install the Linode provider '
              'for Terraform.')
        sys.exit(1)

    hashname = get_hashname(parsed.name)
#   MAJOR @TODO: check here if this hashname already appears as a prefix on any
#   volumes, linodes, or nodebalancers. If it does, bail with an error message,
#   because we don't want to later delete resources from both clusters!

    # print(hashname)

    # Make application directory if it doesn't exist
    appdir = make_appdir("k8s-alpha")
    # Make the terraform project directory if it doesn't exist
    terrapath = os.path.join(appdir, parsed.name)
    safe_mkdir(terrapath)

    # Move to the directory
    os.chdir(terrapath)

    # Generate the terraform file
    terrafile = open('cluster.tf', 'w')
    terrafile.write(gen_terraform_file(context))
    terrafile.close()

    # Run the Terraform commands
    ret = spcall(['terraform', 'workspace', 'new', parsed.name])
    if ret != 0:
        sys.exit(ret)
    ret = spcall(['terraform', 'init'])
    if ret != 0:
        sys.exit(ret)
    ret = spcall(['terraform', 'apply'])
    if ret != 0:
        sys.exit(ret)

    # Merge and/or create kubeconfig for the new cluster.
    # Also, activate the kubeconfig context.
    safe_mkdir(os.path.expanduser("~/.kube"))

    # We expect this to be the path to the generated kubeconfig file
    kubeconfig_new = replace_kubeconfig_user(terrapath, parsed.name)
    kubeconfig_existing = os.path.expanduser("~/.kube/config")
    # Create a merged kubeconfig file and set the context
    # First set up the KUBECONFIG env var so that `kubectl config view --flatten`
    # gives us a new merged config
    os.environ["KUBECONFIG"] = "{}:{}".format(kubeconfig_existing, kubeconfig_new)
    tempfilepath = 'tempkubeconfig'
    tempf = open(tempfilepath, 'w')
    ret = spcall(['kubectl', 'config', 'view', '--flatten'], stdout=tempf)
    if ret != 0:
        sys.exit(ret)
    tempf.close()
    shutil.move(tempfilepath, kubeconfig_existing)

    # Set the kubeconfig context to the new cluster
    spcall(['kubectl', 'config', 'use-context', '{}@{}'.format(parsed.name, parsed.name)])

    # We're done! The user should be able to run something like
    # kubectl get pods --all-namespaces, and see the Linode CSI, CCM etc.

def gen_terraform_file(context):
    return """module "k8s" {{
  source  = "git@github.com:linode/terraform-linode-k8s.git?ref=master"

  linode_token = "{token}"
}}
""".format(
        token=context.token
    )

def replace_kubeconfig_user(terrapath, cluster_name):
    """
    If we leave the user as kubernetes-admin. Then the configs don't flatten properly.
    All of them try to create creds for kubernetes-admin.
    """
    kubeconfig_fp = os.path.join(terrapath, "{}.conf".format(cluster_name))
    kubeconfig = open(kubeconfig_fp).read()
    kubeconfig = kubeconfig.replace('kubernetes-admin', cluster_name)

    kubeconfig_new_fp = os.path.join(terrapath, "{}_new.conf".format(cluster_name))
    kubeconfig_new = open(kubeconfig_new_fp, 'w')
    kubeconfig_new.write(kubeconfig)

    return kubeconfig_new_fp

def pause():
    if sys.version_info[0] < 3:
        raw_input("Press Enter to continue")
    else:
        input("Press Enter to continue")

def make_appdir(appname):
    if sys.platform == 'win32':
        appdir = os.path.join(os.environ['APPDATA'], appname)
    else:
        appdir = os.path.expanduser(os.path.join("~", "." + appname))

    safe_mkdir(appdir)

    return appdir

def safe_mkdir(dirpath):
    if not os.path.isdir(dirpath):
        try:
            os.mkdir(dirpath)
        except:
            print('Unable to create the directory: {}'.format(dirpath))
            sys.exit(1)

def delete(args, context):
    print('deleting cluster')

#def update(args, context):
#    pass
#    # If a user attempts an update but does not have the corresponding
#    # terraform file, point them to a community post on how to retrieve it.

def get_hashname(name):
    """
    A cluster hashname is the first 9 characters of a SHA256 digest encoded in base36.

    This is used as a compact way to uniquely identify a cluster's Linode resources.
    It's also stateless! If a user loses their terraform file and wishes to
    delete a cluster they can still do so.
    """
    hashname = int(hashlib.sha256(name.encode('utf8')).hexdigest(), 16)
    hashname = base36encode(hashname)[:9]
    return hashname

def print_available_commands(commands):
    print("\nAvailable commands:")
    content = [c for c in commands.keys()]
    proc = []
    for i in range(0,len(content),3):
        proc.append(content[i:i+3])
    if content[i+3:]:
        proc.append(content[i+3:])

    table = SingleTable(proc)
    table.inner_heading_row_border = False
    print(table.table)

def base36encode(number):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')
    alphabet='0123456789abcdefghijklmnopqrstuvwxyz'
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36

def base36decode(number):
    return int(number, 36)