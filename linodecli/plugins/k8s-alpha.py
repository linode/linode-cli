"""
The k8s-alpha plugin includes a means to deploy Kubernetes clusters on Linode
"""
import argparse
import base64
import sys
import os
from subprocess import call as spcall, Popen, PIPE
import hashlib
import shutil
from terminaltables import SingleTable

# Alias FileNotFoundError for Python 2
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

plugin_name = os.path.basename(__file__)[:-3]

def call(args, context):
    parser = argparse.ArgumentParser("{}".format(plugin_name), add_help=False)
    parser.add_argument('command', metavar='COMMAND', nargs='?', type=str,
                        help="The {} command to be invoked.".format(plugin_name))
    parsed, args = parser.parse_known_args(args)

    commands = {
        'create': create,
        'delete': delete
    }

    if parsed.command is None or (parsed.command is None and parsed.help):
        parser.print_help()
        print_available_commands(commands)
        sys.exit(0)

    if parsed.command in commands.keys():
        commands[parsed.command](args, context)
    else:
        print('Unrecognized command {}'.format(parsed.command))

def create_varmap(context):
    # Maps parameters for the `create` command to Terraform variable names
    tf_var_map = {
        'node_type': {
            'name': 'server_type_node',
            'default': requested_type_with_fallback(context),
        },
        'nodes': {
            'name': 'nodes',
            'default': 3,
        },
        'master_type': {
            'name': 'server_type_master',
            'default': get_default_master_type(context),
        },
        'region': {
            'name': 'region',
            'default': context.client.config.get_value('region'),
        },
        'ssh_public_key': {
            'name': 'ssh_public_key',
            'default': os.path.expanduser('~/.ssh/id_rsa.pub'),
        },
    }
    return tf_var_map

def create(args, context):
    # Check if deps are installed
    needed_deps = check_deps('terraform', 'kubectl')
    if needed_deps:
        print('To create a cluster, this command requires {}'.format(' and '.join(needed_deps)))
        if 'terraform' in needed_deps:
            print_terraform_install_help()
        if 'kubectl' in needed_deps:
            print_kubectl_install_help()
        sys.exit(1)

    tf_var_map = create_varmap(context)

    parser = argparse.ArgumentParser("{} create".format(plugin_name), add_help=True)
    parser.add_argument('name', metavar='NAME', type=str,
                        help="A name for the cluster.")
#    High availability master nodes coming soon.
#    parser.add_argument('--ha', metavar="MASTERS", type=int, required=False,
#                        choices=[3, 5],
#                        help="Make the cluster highly-available with MASTERS "
#                             "number of masters (3 or 5)")
    parser.add_argument('--node-type', metavar="TYPE", type=str, required=False,
                        default=tf_var_map['node_type']['default'],
                        help='The Linode Type ID for cluster Nodes as retrieved with '
                             '`linode-cli linodes types`. (default "{}")'.format(
                                tf_var_map['node_type']['default']))
    parser.add_argument('--nodes', metavar="COUNT", type=int, required=False,
                        default=tf_var_map['nodes']['default'],
                        help='The number of Linodes to deploy as Nodes in the cluster. '
                             '(default {})'.format(
                                 tf_var_map['nodes']['default']))
    parser.add_argument('--master-type', metavar="TYPE", type=str, required=False,
                        default=tf_var_map['master_type']['default'],
                        help='The Linode Type ID for cluster Master Nodes as retrieved with '
                             '`linode-cli linodes types`. (default "{}")'.format(
                                 tf_var_map['master_type']['default']))
    parser.add_argument('--region', metavar="REGION", type=str, required=False,
                        default=tf_var_map['region']['default'],
                        help='The Linode Region ID in which to deploy the cluster as retrieved '
                             'with `linode-cli regions list`. (default "{}")'.format(
                                 tf_var_map['region']['default']))
    parser.add_argument('--ssh-public-key', metavar="KEYPATH", type=str, required=False,
                        default=tf_var_map['ssh_public_key']['default'],
                        help='The path to your public key file which will be used to access Nodes '
                             'during initial provisioning only! If you don\'t use id_rsa as your '
                             'private key name, use the flag --ssh-public-key and supply your '
                             'public key path. If you use id_rsa as your key name and it\'s been '
                             'added to your ssh-agent, omit the flag. (default {})'.format(tf_var_map['ssh_public_key']['default']))
    parsed, remaining_args = parser.parse_known_args(args)

    # make sure that the ssh public key exists
    check_for_pubkey(parsed)

    # make sure that an ssh-agent is running
    check_for_ssh_agent(parsed)

    if not parsed.region:
        print('You must either configure your default region with '
              '`linode-cli configure` or pass --region')
        sys.exit(1)

    prefix = get_prefix(parsed.name)
#   MAJOR @TODO: check here if this prefix already appears as a prefix on any
#   Volumes, Linodes, or NodeBalancers. If it does, bail with an error message,
#   because we don't want to later delete resources from an existing cluster!
#
#   Luckily, for now, Terraform will refuse to create the Linodes for the new
#   cluster with the same names, stopping the cluster from being created (only in
#   the case where Linodes still exist for an existing cluster). There is still
#   the issue of zombie NodeBalancers to address.

    # Make application directory if it doesn't exist
    appdir = safe_make_appdir("k8s-alpha-linode")
    # Make the terraform project directory if it doesn't exist
    terrapath = os.path.join(appdir, parsed.name)
    safe_mkdir(terrapath)

    # Move to the directory
    os.chdir(terrapath)

    # Generate the terraform file
    terrafile = open('cluster.tf', 'w')
    terrafile.write(gen_terraform_file(context, tf_var_map, parsed.name, prefix))
    terrafile.close()

    # Generate terraform args
    terraform_args = gen_terraform_args(parsed, tf_var_map)

    # Run the Terraform commands
    spcall(['terraform', 'workspace', 'new', parsed.name])
    call_or_exit(['terraform', 'init'])
    # TODO: Before running the apply delete any existing Linodes that would
    # cause the apply to fail.
    terraform_apply_command = ['terraform', 'apply'] + terraform_args + remaining_args
    call_or_exit(terraform_apply_command)

    # Merge and/or create kubeconfig for the new cluster.
    # Also, activate the kubeconfig context.
    safe_mkdir(os.path.expanduser("~/.kube"))

    # We expect this to be the path to the generated kubeconfig file
    kubeconfig_new = replace_kubeconfig_user(terrapath, parsed.name, prefix)
    kubeconfig_existing = os.path.expanduser("~/.kube/config")
    # Create a merged kubeconfig file and set the context
    # First set up the KUBECONFIG env var so that `kubectl config view --flatten`
    # gives us a new merged config
    os.environ["KUBECONFIG"] = "{}:{}".format(kubeconfig_existing, kubeconfig_new)
    tempfilepath = 'tempkubeconfig'
    tempf = open(tempfilepath, 'w')
    call_or_exit(['kubectl', 'config', 'view', '--flatten'], stdout=tempf)
    tempf.close()
    shutil.move(tempfilepath, kubeconfig_existing)

    # Set the kubeconfig context to the new cluster
    call_or_exit(['kubectl', 'config', 'use-context',
                  '{}@{}'.format(get_kubeconfig_user(prefix, parsed.name), parsed.name)])

    print("Your cluster has been created and your kubectl context updated.\n\n"
          "Try the following command: \n"
          "kubectl get pods --all-namespaces\n\n"
          "Come hang out with us in #linode on the Kubernetes Slack! http://slack.k8s.io/")

    # We're done! We have merged the user's kubeconfigs.
    # The user should be able to run something like
    # `kubectl get pods --all-namespaces`
    # and see the Linode CSI, CCM, and ExternalDNS controllers

def delete(args, context):
    needed_deps = check_deps('terraform')
    if needed_deps:
        print('This command requires {}\n'.format(' and '.join(needed_deps)))
        if 'terraform' in needed_deps:
            print_terraform_install_help()
        sys.exit(1)

    parser = argparse.ArgumentParser("{} create".format(plugin_name), add_help=True)
    parser.add_argument('name', metavar='NAME', type=str,
                        help="The name of the cluster to delete.")
    parsed, remaining_args = parser.parse_known_args(args)

    # Get the appdir path
    appdir = safe_make_appdir("k8s-alpha-linode")
    terrapath = os.path.join(appdir, parsed.name)
    # Move to the terraform directory
    os.chdir(terrapath)
    call_or_exit(['terraform', 'destroy'] + remaining_args)

    # TODO: Also delete all NodeBalancers and Volumes using the cluster prefix

def check_for_pubkey(parsed):
    try:
        open(parsed.ssh_public_key, 'r')
    except FileNotFoundError:
        print("The ssh public key {} does not exist\n"
              "Please refer to this documentation on creating an ssh key\n"
              "https://help.github.com/articles/"
              "generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/".format(
                  parsed.ssh_public_key
              ))
        sys.exit(1)

def check_for_ssh_agent(parsed):
    """Check if the selected pubkey is added to the agent"""

    with open(parsed.ssh_public_key) as f:
        """Grab the actual pubkey from the file"""
        pubkey = f.readline().split(' ')[1]

    print_warning = False
    need_agent_start = False
    try:
        # ssh-agent -L (not -l), which prints the actual pubkeys rather than just the comments
        pid = Popen(["ssh-add", "-L"], stdout=PIPE, stderr=PIPE)
        stdout, _ = pid.communicate()
        stdout = str(stdout)
        if pid.returncode == 2:
            need_agent_start = True
        # If the pubkey isn't there, then it's not loaded!
        if pubkey not in stdout:
            print_warning = True
    except FileNotFoundError:
        print_warning = True
        need_agent_start = True

    if print_warning:
        print_ssh_agent_warning(parsed, with_agent_start=need_agent_start)

def print_ssh_agent_warning(parsed, with_agent_start=False):
    agent_start = ''
    if with_agent_start:
        agent_start = "eval $(ssh-agent) && "
    print("Your currently selected ssh public key is: {}\n"
          "Use --ssh-public-key to choose a different public key.\n\n"
          "The ssh private key must be added to your ssh-agent.\n"
          "Please run this command:\n\n{}ssh-add {}".format(
              parsed.ssh_public_key,
              agent_start,
              parsed.ssh_public_key.replace('.pub', '')))
    sys.exit(1)

def check_deps(*args):
    needed_deps = []
    for dep in args:
        if not dep_installed(dep):
            needed_deps.append(dep)
    return needed_deps

def dep_installed(command):
    try:
        nullf = open(os.devnull, 'w')
        spcall([command], stdout=nullf)
        nullf.close()
        return True
    except: 
        return False

def print_terraform_install_help():
    print('\n# Installing Terraform:\n\n'
          'On macOS with Homebrew: \n'
          'brew install terraform\n\n'
          'For other platforms, use your package manager and/or refer to this documentation\n'
          'https://learn.hashicorp.com/terraform/getting-started/install.html')

def print_kubectl_install_help():
    print('\n# Installing The Kubernetes CLI (kubectl):\n\n'
          'On macOS with Homebrew: \n'
          'brew install kubernetes-cli\n\n'
          'For other platforms, use your package manager and/or refer to this documentation\n'
          'https://kubernetes.io/docs/tasks/tools/install-kubectl/')

def bare_int_or_quoted_value(val):
    if isinstance(val, int):
        return val
    # a way to check for str or unicode type in both Python2/3
    elif isinstance(val, ("".__class__, u"".__class__)):
        return '"{}"'.format(val)
    else:
        # Important that we return this string rather than an empty string
        # because the callee expects some non-empty value
        return '""'

def gen_terraform_file(context, tf_var_map, cluster_name, prefix):
    tf_file_parts = []

    for varname in tf_var_map.keys():
        tf_file_parts.append("""variable "{tf_varname}" {{
  default = {default}
}}
""".format(tf_varname=tf_var_map[varname]['name'],
           default=bare_int_or_quoted_value(tf_var_map[varname]['default'])))

    tf_file_parts.append("""module "k8s" {{
  source  = "git::https://github.com/linode/terraform-linode-k8s.git?ref=for-cli"

  linode_token = "{token}"
  
  linode_group = "{prefix}-{cluster_name}"
""".format(token=context.token,
           prefix=prefix,
           cluster_name=cluster_name,))

    for varname in tf_var_map.keys():
        tf_file_parts.append("""
  {tf_varname} = "${{var.{tf_varname}}}"
""".format(tf_varname=tf_var_map[varname]['name']))

    tf_file_parts.append("}\n")

    return ''.join(tf_file_parts)

def gen_terraform_args(parsed, tf_var_map):
    'Transform relevant cli plugin args into terraform args'
    args = []
    for varname in tf_var_map.keys():
        args = args + [
            '-var',
            "{}={}".format(tf_var_map[varname]['name'],
            getattr(parsed, varname))]
    return args

def call_or_exit(*args, **kwargs):
    ret = spcall(*args, **kwargs)
    if ret != 0:
        print("Error when calling {} with additional options {}".format(args, kwargs))
        print("\nPlease visit us in #linode on the Kubernetes Slack and let us know about "
              "this error! http://slack.k8s.io/")
        sys.exit(ret)

def get_kubeconfig_user(cluster_name, prefix):
    return "{}-{}".format(prefix, cluster_name)

def replace_kubeconfig_user(terrapath, cluster_name, prefix):
    """
    If we leave the user as kubernetes-admin then the configs don't flatten properly.
    All of them try to create creds for kubernetes-admin.
    """
    kubeconfig_fp = os.path.join(terrapath, "{}.conf".format(cluster_name))
    with open(kubeconfig_fp) as f:
        kubeconfig = f.read()
    
    kubeconfig = kubeconfig.replace('kubernetes-admin', get_kubeconfig_user(prefix, cluster_name))

    kubeconfig_new_fp = os.path.join(terrapath, "{}_new.conf".format(cluster_name))
    with open(kubeconfig_new_fp, 'w') as f:
        f.write(kubeconfig)

    return kubeconfig_new_fp

def safe_make_appdir(appname):
    if sys.platform == 'win32':
        appdir = os.path.join(os.environ['APPDATA'], appname)
    else:
        appdir = os.path.expanduser(os.path.join("~", "." + appname))

    if not appdir:
        print('Cannot locate an appropriate directory in which to store data: "{}"'.format(appdir))
        sys.exit(1)

    safe_mkdir(appdir)

    return appdir

def safe_mkdir(dirpath):
    if not os.path.isdir(dirpath):
        try:
            os.mkdir(dirpath)
        except:
            print('Unable to create the directory: {}'.format(dirpath))
            sys.exit(1)

def get_prefix(name):
    return 'ka{}'.format(get_hashname(name))

def get_hashname(name):
    """
    A cluster hashname is the first 9 characters of a SHA256 digest encoded in base64

    This is used as a compact way to uniquely identify a cluster's Linode resources.
    It's also stateless! If a user loses their terraform file and wishes to
    delete a cluster they can still do so.
    """
    hashname = base64.b64encode(hashlib.sha256(name.encode('utf8')).digest())
    hashname = hashname.decode('utf8')
    hashname = hashname.replace('+', '')
    hashname = hashname.replace('/', '')
    return hashname[:9]

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

def get_default_master_type(context):
    """
    Return either the user's requeted default type size (if valid for
    a Kubernetes master) or the smallest valid type for a Kubernetes
    master if the user's requested type doesn't meet that criteria.

    If the user's type doesn't meet the 2 VCPU requirement, it's
    probably a smaller type, so we default to the smallest valid type
    in that case to get as close as possible to their requested type.
    """
    requested_default = requested_type_with_fallback(context)

    if requested_default:
        if is_valid_master_type(context, requested_default):
            return requested_default

    return smallest_valid_master(context)

def requested_type_with_fallback(context):
    default_node_type = 'g6-standard-2'
    try:
        requested_node_type = context.client.config.get_value('type')
        if not requested_node_type:
            raise ValueError('user did not provide a Linode type by argument or config')
        return requested_node_type
    except:
        pass
    return default_node_type

def is_valid_master_type(context, linode_type):
    """
    Kubernetes masters must have a minimum of 2 VCPUs.
    """
    status, result = context.client.call_operation('linodes', 'type-view', args=[linode_type])
    if status != 200:
        raise RuntimeError(
            "{}: Failed to look up configured default Linode type from API".format(str(status)))
    else:
        return result['vcpus'] >= 2

def smallest_valid_master(context):
    status, result = context.client.call_operation('linodes', 'types',
        filters={
            "+and": [{ "vcpus": { "+gte": 2 }}, {"class": "standard"}],
            "+order_by": "memory", "+order": "asc"})
    if status != 200:
        raise RuntimeError("{}: Failed to request Linode types from API".format(str(status)))
    else:
        return result['data'][0]['id']
