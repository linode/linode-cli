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

        if not self.config.has_option('DEFAULT', 'default-user') and self.config.has_option('DEFAULT', 'token'):
            self._handle_no_default_user()

        if (not self.config.has_option('DEFAULT', 'default-user')
            and not skip_config and not os.environ.get(ENV_TOKEN_NAME, None)):
            self.configure()

    def set_user(self, username):
        """
        Sets the acting username.  If this username is not in the config, this is
        an error.  This overrides the default username
        """
        if not self.config.has_section(username):
            print('User {} is not configured!'.format(username))
            sys.exit(1)

        self.username = username

    def default_username(self):
        return self.config.get('DEFAULT', 'default-user')

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

    def update(self, namespace):
        """
        This updates a Namespace (as returned by ArgumentParser) with config values
        if they aren't present in the Namespace already.
        """
        username = self.username or self.default_username()

        if not self.config.has_option(username, 'token') and not os.environ.get(ENV_TOKEN_NAME, None):
            print("User {} is not configured.".format(username))
            sys.exit(1)

        return self.update_namespace(namespace, dict(self.config.items(username)))

    def get_token(self):
        """
        Returns the token for a configured user
        """
        t = os.environ.get(ENV_TOKEN_NAME, None)
        return t if t else self.config.get(self.username or self.default_username(), "token")

    def remove_user(self, username):
        """
        Removes the requested user from the config.  If the user is the default,
        this exits with error
        """
        if self.default_username() == username:
            print('Cannot remote {} as they are the default user!  You can change '
                  'the default user with: `linode-cli set-user USERNAME`'.format(username))
            sys.exit(1)

        if self.config.has_section(username):
            self.config.remove_section(username)
            self._write_config()

    def print_users(self):
        """
        Prints all users available and exits
        """
        print('Configured Users: ')
        default_user = self.default_username()

        for sec in self.config.sections():
            if sec != 'DEFAULT':
                print('{}  {}'.format('*' if sec == default_user else ' ', sec))

        sys.exit(0)

    def set_default_user(self, username):
        """
        Sets the default user.  If that user isn't in the config, exits with error
        """
        if not self.config.has_section(username):
            print('User {} is not configured!'.format(username))
            sys.exit(1)

        self.config.set('DEFAULT', 'default-user', username)
        self._write_config()

    def configure(self):
        """
        This assumes we're running interactively, and prompts the user
        for a series of defaults in order to make future CLI calls
        easier.  This also sets up the config file.
        """
        # If configuration has already been done in this run, don't do it again.
        if self._configured: return
        config = {}
        # we're configuring the default user if there is no default user configured
        # yet
        is_default = not self.config.has_option('DEFAULT', 'default-user')
        username = None

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

                username = u['username']
                print()
                print('Configuring {}'.format(username))
                print()
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

        if not is_default:
            while True:
                value = input_helper('Make active user? [y/N]: ')

                if value.lower() in 'yn':
                    is_default = value.lower() == 'y'
                    break
                elif not value.strip():
                    break

            if not is_default: # they didn't change the default user
                print('Active user will remain {}'.format(self.config.get('DEFAULT', 'default-user')))


        if is_default:
            # if this is the default user, make it so
            self.config.set('DEFAULT', 'default-user', username)
            print('Active user is now {}'.format(username))

        for k, v in config.items():
            if v:
                self.config.set(username, k, v)

        self._write_config()
        os.chmod(self._get_config_path(), 0o600)
        self._configured = True

    def _write_config(self, silent=False):
        """
        Saves the config file as it is right now
        """
        with open(self._get_config_path(), 'w') as f:
            self.config.write(f)

        if not silent:
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

    def _handle_no_default_user(self):
        """
        Handle the case that there is no default user in the config
        """
        users = [c for c in self.config.sections() if c != 'DEFAULT']

        if len(users) == 1:
            # only one user configured - they're the default
            self.config.set('DEFAULT', 'default-user', users[0])
            self._write_config(silent=True)
            return

        if len(users) == 0:
            # config is new or _really_ old
            token = self.config.get('DEFAULT', 'token')

            if token is not None:
                # there's a token in the config - configure that user
                u = self._do_get_request('/profile', token=token, exit_on_error=False)

                if "errors" in u:
                    # this token was bad - reconfigure
                    self.configure()
                    return

                # setup config for this user
                username = u['username']

                self.config.set('DEFAULT', 'default-user', username)
                self.config.add_section(username)
                self.config.set(username, 'token', token)
                self.config.set(username, 'region', self.config.get('DEFAULT', 'region'))
                self.config.set(username, 'type', self.config.get('DEFAULT', 'type'))
                self.config.set(username, 'image', self.config.get('DEFAULT', 'image'))

                self._write_config(silent=True)
            else:
                # got nothin', reconfigure
                self.configure()

            # this should be handled
            return

        # more than one user - prompt for the default
        print('Please choose the active user.  Configured users are:')
        for u in users:
            print(' {}'.format(u))
        print()

        while True:
            username = input_helper('Active user: ')

            if username in users:
                self.config.set('DEFAULT', 'default-user', username)
                self._write_config()
                return
            print('No user {}'.format(username))
