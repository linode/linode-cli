import argparse
import configparser
import os
import sys

import linode

# TODO - cross-platform concerns
CONFIG_DIR = os.path.expanduser('~')
CONFIG_NAME = '.linode-cli'

def _get_config_path():
    return "{}/{}".format(CONFIG_DIR, CONFIG_NAME)

def _default_thing_input(ask, things, prompt, error, optional=True):
    print('\n{}  Choices are:'.format(ask))
    for ind, thing in enumerate(things):
        print(" {} - {}".format(ind+1, thing.id))
    print()

    ret = ''
    while True:
        choice = input(prompt)

        if choice:
            try:
                choice = int(choice)
                choice = things[choice-1].id
            except:
                pass

            if choice in [ thing.id for thing in things ]:
                ret = choice
                break
            print(error)
        else:
            if optional:
                break
            else:
                print(error)
    return ret

def _get_config():
    conf = configparser.ConfigParser()
    conf.read(_get_config_path())
    return conf

def configure(username=None):
    """
    This assumes we're running interactively, and prompts the user
    for a series of defaults in order to make future CLI calls
    easier.  This also sets up the config file.
    """
    config = {}
    is_default = username == None

    # get the token
    login_client = linode.LinodeLoginClient('','')

    print("""Welcome to the Linode CLI.  This will walk you through some
initial setup.

First, we need a Personal Access Token.  To get one, please visit
https://cloud.linode.com/profile/tokens and click
"Create a Personal Access Token".  The CLI needs access to everything
on your account to work correctly.
""")

    client = None
    while True:
        config['token'] = input("Personal Access Token: ")

        client = linode.LinodeClient(config['token'])
        try:
            u = client.get_profile()
            if not username:
                username = u.username
            elif not u.username == username:
                print("That is a token for {}, not {}\n".format(u.username, username))
                continue
            break
        except:
            print("That token didn't work, please enter a working Personal Access Token.\n")

    # get the preferred things
    config['location'] = _default_thing_input(
        'Default Region for deploying Linodes.',
        client.get_regions(),
        'Default Datacenter (Optional): ',
        'Please select a valid region, or press Enter to skip')
                
    config['plan'] = _default_thing_input(
        'Default type of Linode to deploy.',
        client.linode.get_types(),
        'Default type of Linode (Optional): ', 'Please select a valid Type, or press Enter to skip')

    config['image'] = _default_thing_input(
        'Default Image to deploy to new Linodes.',
        client.get_images(linode.Image.is_public==True),
        'Default Image (Optional): ',
        'Please select a valid Image, or press Enter to skip')

    config['pubkey_file'] = ''
    print()
    while True:
        keypath = input("Path to SSH public key to deploy to new Linodes (Optional): ")

        if keypath:
            keypath = os.path.expanduser(keypath)
            if os.path.isfile(keypath):
                with open(keypath) as keyfile:
                    k = keyfile.read()
                    if k.startswith("ssh-rsa"):
                        config['pubkey_file'] = keypath
                        break
                    print("Invalid public key.  Please enter a path to a SSH public key file, or press Enter to skip.")
            else:
                print("File not found.  Please enter a path to a SSH public key file, or press Enter to skip.")
        else:
            break

    conf = configparser.ConfigParser()

    cdict = _get_config()
    cdict[username]=config
    if is_default:
        cdict['DEFAULT'] = config

    conf.read_dict(cdict)
    with open(_get_config_path(), 'w') as f:
        conf.write(f)

    print("\nConfig written to {}".format(_get_config_path()))

def update_namespace(namespace, new_dict):
    """
    In order to update the namespace, we need to turn it into a dict, modify it there,
    then reconstruct it with the exploded dict.
    """
    ns_dict = vars(namespace)
    for k in new_dict:
        if not k in ns_dict or not ns_dict[k]:
            ns_dict[k] = new_dict[k]

    return argparse.Namespace(**ns_dict)
    

def update(namespace, username=None):
    """
    This updates a Namespace (as returned by ArgumentParser) with config values
    if they aren't present in the Namespace already.
    """
    if not os.path.isfile(_get_config_path()):
        return namespace

    if not username:
        username = "DEFAULT"

    conf = _get_config()

    if not username in conf:
        print("User {} is not configured.".format(username))
        sys.exit(1)

    # update old config items to use new names
    if 'image' not in conf[username] and 'distribution' in conf[username]:
        conf[username]['image'] = conf[username]['distribution']

        with open(_get_config_path(), 'w') as f:
            conf.write(f)

    return update_namespace(namespace, conf[username])
