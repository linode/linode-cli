"""
Handles configuring the cli, as well as loading configs so that they can be
used elsewhere.
"""
from __future__ import print_function

import argparse
try:
    # python3
    import configparser
except ImportError:
    # python2
    import ConfigParser as configparser
from requests import get
import os
import sys

ENV_TOKEN_NAME='LINODE_CLI_TOKEN'

CONFIG_DIR = os.path.expanduser('~')
CONFIG_NAME = '.linode-cli'
TOKEN_GENERATION_URL='https://cloud.linode.com/profile/tokens'


def input_helper(prompt):
    """
    Handles python2 and python3 differences in input command
    """
    if sys.version_info[0] == 2:
        # python2 input is scary - we want raw_input
        return raw_input(prompt)
    else:
        return input(prompt)

class CLIConfig:
    def __init__(self, base_url, username=None, skip_config=False):
        self.base_url = base_url
        self.username = username
        self.config = self._get_config()

        self._configured = False

        if not self.config.has_option('DEFAULT', 'token') and not skip_config and not os.environ.get(ENV_TOKEN_NAME, None):
            self.configure()

    def update_namespace(self, namespace, new_dict):
        """
        In order to update the namespace, we need to turn it into a dict, modify it there,
        then reconstruct it with the exploded dict.
        """
        ns_dict = vars(namespace)
        for k in new_dict:
            if k in ns_dict and ns_dict[k] is None:
                ns_dict[k] = new_dict[k]

        return argparse.Namespace(**ns_dict)

    def update(self, namespace, username=None):
        """
        This updates a Namespace (as returned by ArgumentParser) with config values
        if they aren't present in the Namespace already.
        """
        if not username:
            username = "DEFAULT"

        if not self.config.has_option(username, 'token'):
            print("User {} is not configured.".format(username))
            sys.exit(1)

        return self.update_namespace(namespace, dict(self.config.items(username)))

    def get_token(self, username=None):
        """
        Returns the token for a configured user
        """
        t = os.environ.get(ENV_TOKEN_NAME, None)
        return t if t else self.config.get(username or 'DEFAULT', "token")

    def configure(self, username=None):
        """
        This assumes we're running interactively, and prompts the user
        for a series of defaults in order to make future CLI calls
        easier.  This also sets up the config file.
        """
        # If configuration has already been done in this run, don't do it again.
        if self._configured: return
        config = {}
        is_default = username == None

        print("""Welcome to the Linode CLI.  This will walk you through some
initial setup.""")

        if ENV_TOKEN_NAME in os.environ:
            print("""Using token from LINODE_TOKEN.
Note that no token will be saved in your configuration file.
    * If you lose or remove LINODE_TOKEN, Linode CLI will stop working.
    * All profiles will use LINODE_TOKEN.""")
            username = 'DEFAULT'

        else:
            print("""
First, we need a Personal Access Token.  To get one, please visit
{} and click
"Add a Personal Access Token".  The CLI needs access to everything
on your account to work correctly.""".format(TOKEN_GENERATION_URL))

            while True:
                config['token'] = input_helper("Personal Access Token: ")

                u = self._do_get_request('/profile', token=config['token'], exit_on_error=False)
                if "errors" in u:
                    print("That token didn't work: {}".format(','.join([c["reason"] for c in u['errors']])))
                    continue

                if username is None:
                    username = u['username']
                elif u['username'] != username:
                    print("That is a token for {}, not {}\n".format(u['username'], username))
                    continue
                break

        regions = [r['id'] for r in self._do_get_request('/regions')['data']]
        types = [t['id'] for t in self._do_get_request('/linode/types')['data']]
        images = [i['id'] for i in self._do_get_request('/images')['data']]

        # get the preferred things
        config['region'] = self._default_thing_input(
            'Default Region for operations.',
            regions,
            'Default Region (Optional): ',
            'Please select a valid Region, or press Enter to skip')

        config['type'] = self._default_thing_input(
            'Default Type of Linode to deploy.',
            types,
            'Default Type of Linode (Optional): ',
            'Please select a valid Type, or press Enter to skip')

        config['image'] = self._default_thing_input(
            'Default Image to deploy to new Linodes.',
            images,
            'Default Image (Optional): ',
            'Please select a valid Image, or press Enter to skip')

        # save off the new configuration
        if username != 'DEFAULT' and not self.config.has_section(username):
            self.config.add_section(username)

        for k, v in config.items():
            self.config.set(username, k, v)
            if is_default:
                self.config.set('DEFAULT', k, v)

        with open(self._get_config_path(), 'w') as f:
            self.config.write(f)
        os.chmod(self._get_config_path(), 0o600)
        self._configured = True

        print("\nConfig written to {}".format(self._get_config_path()))

    def _get_config_path(self):
        """
        Returns the path to the config file
        """
        return "{}/{}".format(CONFIG_DIR, CONFIG_NAME)

    def _get_config(self):
        conf = configparser.ConfigParser()
        conf.read(self._get_config_path())
        return conf

    def _default_thing_input(self, ask, things, prompt, error, optional=True):
        """
        Requests the user choose from a list of things with the given prompt and
        error if they choose something invalid.  If optional, the user may hit
        enter to not configure this option.
        """
        print('\n{}  Choices are:'.format(ask))
        for ind, thing in enumerate(things):
            print(" {} - {}".format(ind+1, thing))
        print()

        ret = ''
        while True:
            choice = input_helper(prompt)

            if choice:
                try:
                    choice = int(choice)
                    choice = things[choice-1]
                except:
                    pass

                if choice in [thing for thing in things]:
                    ret = choice
                    break
                print(error)
            else:
                if optional:
                    break
                else:
                    print(error)
        return ret

    def _do_get_request(self, url, token=None, exit_on_error=True):
        """
        Does helper requests during configuration
        """
        headers = {}

        if token is not None:
            headers["Authorization"] = "Bearer {}".format(token)

        result = get(self.base_url+url, headers=headers)

        if not 199 < result.status_code < 300:
            print("Could not contact {} - Error: {}".format(self.base_url+url,
                                                             result.status_code))
            if exit_on_error:
                sys.exit(4)

        return result.json()
