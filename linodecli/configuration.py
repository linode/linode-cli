"""
Handles configuring the cli, as well as loading configs so that they can be
used elsewhere.
"""
from __future__ import print_function

import argparse
from datetime import datetime
import re
from http import server
import socket
import webbrowser
try:
    # python3
    import configparser
except ImportError:
    # python2
    import ConfigParser as configparser
import requests
import os
import sys

ENV_TOKEN_NAME='LINODE_CLI_TOKEN'

LEGACY_CONFIG_DIR = os.path.expanduser('~')
LEGACY_CONFIG_NAME = '.linode-cli'
CONFIG_DIR = os.environ.get('XDG_CONFIG_HOME', "{}/{}".format(os.path.expanduser('~'), '.config'))

CONFIG_NAME = 'linode-cli'
TOKEN_GENERATION_URL='https://cloud.linode.com/profile/tokens'

# This is used for web-based configuration
OAUTH_CLIENT_ID = '5823b4627e45411d18e9'

# this is a list of browser that _should_ work for web-based auth.  This is mostly
# intended to exclude lynx and other terminal browsers which could be opened, but
# won't work.
KNOWN_GOOD_BROWSERS = set(('chrome', 'firefox', 'mozilla', 'netscape', 'opera', 'safari', 'chromium', 'chromium-browser', 'epiphany'))

# in the event that we can't load the styled landing page from file, this will
# do as a landing page
DEFAULT_LANDING_PAGE = """
<h2>Success</h2><br/><p>You may return to your terminal to continue..</p>
<script>
// this is gross, sorry
let r = new XMLHttpRequest('http://localhost:{port}');
r.open('GET', '/token/'+window.location.hash.substr(1));
r.send();
</script>
"""


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
        self.config = self._get_config(load=not skip_config)
        self.running_plugin = None
        self.used_env_token = False

        self._configured = False

        self.configure_with_pat = "--token" in sys.argv

        if not skip_config and not self.config.has_option('DEFAULT', 'default-user') and self.config.has_option('DEFAULT', 'token'):
            self._handle_no_default_user()

        environ_token = os.environ.get(ENV_TOKEN_NAME, None)

        if (not self.config.has_option('DEFAULT', 'default-user')
            and not skip_config and not environ_token):
            self.configure()
        elif environ_token:
            self.used_env_token = True

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
        if self.config.has_option('DEFAULT', "default-user"):
            return self.config.get('DEFAULT', 'default-user')
        return ""

    def update_namespace(self, namespace, new_dict):
        """
        In order to update the namespace, we need to turn it into a dict, modify it there,
        then reconstruct it with the exploded dict.
        """
        ns_dict = vars(namespace)
        for k in new_dict:
            if k.startswith('plugin-'):
                # plugins set config options that start with 'plugin-' - these don't
                # get included in the updated namespace
                continue
            if k in ns_dict and ns_dict[k] is None:
                ns_dict[k] = new_dict[k]

        return argparse.Namespace(**ns_dict)

    def update(self, namespace):
        """
        This updates a Namespace (as returned by ArgumentParser) with config values
        if they aren't present in the Namespace already.
        """
        if self.used_env_token and self.config is None:
            # the CLI is using a token defined in the environment; as such, we may
            # not have actually loaded a config file.  That's fine, there are just
            # no defaults
            return

        username = self.username or self.default_username()

        if not self.config.has_option(username, 'token') and not os.environ.get(ENV_TOKEN_NAME, None):
            print("User {} is not configured.".format(username))
            sys.exit(1)

        if self.config.has_section(username):
            return self.update_namespace(namespace, dict(self.config.items(username)))
        return namespace

    def get_token(self):
        """
        Returns the token for a configured user
        """
        if self.used_env_token:
            return os.environ.get(ENV_TOKEN_NAME, None)

        if self.config.has_option(self.username or self.default_username(), "token"):
            return self.config.get(self.username or self.default_username(), "token")
        return ""

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
            self.write_config()

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
        self.write_config()

    # plugin methods - these are intended for plugins to utilize to store their
    # own persistent config information
    def get_value(self, key):
        """
        Retrieves and returns an existing config value for the current user.  This
        is intended for plugins to use instead of having to deal with figuring out
        who the current user is when accessing their config.

        .. warning::
           Plugins _MUST NOT_ set values for the user's config except through
           ``plugin_set_value`` below.

        :param key: The key to look up.
        :type key: str

        :returns: The value for that key, or None if the key doesn't exist for the
                  current user.
        :rtype: any
        """
        username = self.username or self.default_username()

        if not self.config.has_option(username, key):
            return None

        return self.config.get(username, key)

    def plugin_set_value(self, key, value):
        """
        Sets a new config value for a plugin for the current user.  Plugin config
        keys are set in the following format::

           plugin-{plugin_name}-{key}

        Values set with this method are intended to be retrieved with ``plugin_get_value``
        below.

        :param key: The config key to set - this is needed to retrieve the value
        :type key: str
        :param value: The value to set for this key
        :type value: any
        """
        if self.running_plugin is None:
            raise RuntimeError('No running plugin to retrieve configuration for!')

        username = self.username or self.default_username()
        self.config.set(username, 'plugin-{}-{}'.format(self.running_plugin, key), value)

    def plugin_get_value(self, key):
        """
        Retrieves and returns a config value previously set for a plugin.  Your
        plugin should have set this value in the past.  If this value does not
        exist in the config, ``None`` is returned.  This is the only time
        ``None`` is returned, so receiving this value should be treated as
        "plugin is not configured."

        :param key: The key of the value to return
        :type key: str

        :returns: The value for this plugin for this key, or None if not set
        :rtype: any
        """
        if self.running_plugin is None:
            raise RuntimeError('No running plugin to retrieve configuration for!')

        username = self.username or self.default_username()
        full_key = 'plugin-{}-{}'.format(self.running_plugin, key)

        if not self.config.has_option(username, full_key):
            return None

        return self.config.get(username, full_key)

    def write_config(self, silent=False):
        """
        Saves the config file as it is right now.  This can be used by plugins
        to save values they've set, and is used internally to update the config
        on disk when a new user if configured.

        :param silent: If True, does not print a message noting the config file
                       has been updated.  This is primarily intended for silently
                       updated the config file from one version to another.
        :type silent: bool
        """


        # Create the ~/.config directory if it does not exist
        if not os.path.exists("{}/{}".format(os.path.expanduser('~'), '.config')):
            os.makedirs("{}/{}".format(os.path.expanduser('~'), '.config'))

        with open(self._get_config_path(), 'w') as f:
            self.config.write(f)

        if not silent:
            print("\nConfig written to {}".format(self._get_config_path()))

    def _username_for_token(self, token):
        """
        A helper function that returns the username assocaited with a token by
        requesting it from the API
        """
        u = self._do_get_request('/profile', token=token, exit_on_error=False)
        if "errors" in u:
            print("That token didn't work: {}".format(','.join([c["reason"] for c in u['errors']])))
            return None

        return u['username']

    def _get_token_terminal(self):
        """
        Handles prompting the user for a Personal Access Token and checking it
        to ensure it works.
        """
        print("""
First, we need a Personal Access Token.  To get one, please visit
{} and click
"Create a Personal Access Token".  The CLI needs access to everything
on your account to work correctly.""".format(TOKEN_GENERATION_URL))

        while True:
            token = input_helper("Personal Access Token: ")

            username = self._username_for_token(token)
            if username is not None:
                break

        return username, token

    def _get_token_web(self):
        """
        Handles OAuth authentication for the CLI.  This requires us to get a temporary
        token over OAuth and then use it to create a permanent token for the CLI.
        This function returns the token the CLI should use, or exits if anything
        goes wrong.
        """
        temp_token = self._handle_oauth_callback()
        username = self._username_for_token(temp_token)

        if username is None:
            print("OAuth failed.  Please try again of use a token for auth.")
            sys.exit(1)

        # the token returned via public oauth will expire in 2 hours, which
        # isn't great.  Instead, we're gonna make a token that expires never
        # and store that.
        result = self._do_request(
            requests.post,
            "/profile/tokens",
            token=temp_token,
            # generate the actual token with a label like:
            #  Linode CLI @ linode
            # The creation date is already recoreded with the token, so
            # this should be all the relevant info.
            body={"label":"Linode CLI @ {}".format(
                socket.gethostname()
            )}
        )

        return username, result['token']

    def _handle_oauth_callback(self):
        """
        Sends the user to a URL to perform an OAuth login for the CLI, then redirets
        them to a locally-hosted page that captures teh token
        """
        # load up landing page HTML
        landing_page_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "oauth-landing-page.html")

        try:
            with open(landing_page_path) as f:
                landing_page = f.read()
        except:
            landing_page = DEFAULT_LANDING_PAGE

        class Handler(server.BaseHTTPRequestHandler):
            """
            The issue here is that Login sends the token in the URL hash, meaning
            that we cannot see it on the server side.  An attempt was made to
            get the client (browser) to send an ajax request to pass it along,
            but that's pretty gross and also isn't working.  Needs more thought.
            """
            def do_GET(self):
                if "token" in self.path:
                    # we got a token!  Parse it out of the request
                    token_part = self.path.split('/', 2)[2]

                    m = re.search(r'access_token=([a-z0-9]+)', token_part)
                    if m and len(m.groups()):
                        self.server.token = m.groups()[0]

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                # TODO: Clean up this page and make it look nice
                self.wfile.write(bytes(landing_page.format(port=self.server.server_address[1]).encode("utf-8")))

            def log_message(self, form, *args):
                """Don't actually log the request"""

        # start a server to catch the response
        serv = server.HTTPServer(("localhost",0), Handler)
        serv.token = None

        # figure out the URL to direct the user to and print out the prompt
        url = "https://login.linode.com/oauth/authorize?client_id={}&response_type=token&scopes=*&redirect_uri=http://localhost:{}".format(
            OAUTH_CLIENT_ID, serv.server_address[1]
        )
        print("""A browser should open directing you to this URL to authenticate:

{}

If you are not automatically directed there, please copy/paste the link into your browser
to continue..
""".format(url))


        webbrowser.open(url)

        try:
            while serv.token is None:
                # serve requests one at a time until we get a token or are interrupted
                serv.handle_request()
        except KeyboardInterrupt:
            print()
            print("Giving up.  If you couldn't get web authentication to work, please "
                  "try token using a token by invoking with `linode-cli configure --token`, "
                  "and open an issue at https://github.com/linode/linode-cli")
            sys.exit(1)

        return serv.token

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

        print("""Welcome to the Linode CLI.  This will walk you through some initial setup.""")

        if ENV_TOKEN_NAME in os.environ:
            print("""Using token from {env_token_name}.
Note that no token will be saved in your configuration file.
    * If you lose or remove {env_token_name}.
    * All profiles will use {env_token_name}.""".format(env_token_name=ENV_TOKEN_NAME))
            username = 'DEFAULT'

        else:
            # let's see if we _can_ use web
            can_use_browser = True
            try:
                webbrowser.get()
            except webbrowser.Error:
                # there are no browsers installed
                 can_use_browser = False

            if can_use_browser and not KNOWN_GOOD_BROWSERS.intersection(webbrowser._tryorder):
                print()
                print("This tool defaults to web-based authentication, however "
                      "no known-working browsers were found.")

                while True:
                    r = input_helper("Try it anyway? [y/N]: ")
                    if r.lower() in 'yn ':
                        can_use_browser = r.lower() == 'y'
                        break

            if self.configure_with_pat or not can_use_browser:
                username, config['token'] = self._get_token_terminal()
            else:
                print()
                print("The CLI will use its web-based authentication to log you in.  "
                      "If you prefer to supply a Personal Access Token, use `linode-cli configure --token`. ")
                print()
                input_helper("Press enter to continue.  This will open a browser and proceed with authentication.")
                username, config['token'] = self._get_token_web()

        print()
        print('Configuring {}'.format(username))
        print()

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
            if username != self.default_username():
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

        self.write_config()
        os.chmod(self._get_config_path(), 0o600)
        self._configured = True

    def _get_config_path(self):
        """
        Returns the path to the config file.
        """
        if os.path.exists("{}/{}".format(LEGACY_CONFIG_DIR, LEGACY_CONFIG_NAME)):
            return "{}/{}".format(LEGACY_CONFIG_DIR, LEGACY_CONFIG_NAME)


        return "{}/{}".format(CONFIG_DIR, CONFIG_NAME)

    def _get_config(self, load=True):
        """
        Returns a new ConfigParser object that represents the CLI's configuration.
        If load is false, we won't load the config from disk.

        :param load: If True, load the config from the default path.  Otherwise,
                     don't (and just return an empty ConfigParser)
        :type load: bool
        """
        conf = configparser.ConfigParser()

        if load:
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
        Does helper get requests during configuration
        """
        return self._do_request(requests.get, url, token=token, exit_on_error=exit_on_error)

    def _do_request(self, method, url, token=None, exit_on_error=None, body=None):
        """
        Does helper requests during configuration
        """
        headers = {}

        if token is not None:
            headers["Authorization"] = "Bearer {}".format(token)
            headers["Content-type"] = "application/json"

        result = method(self.base_url+url, headers=headers, json=body)

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
            self.write_config(silent=True)
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

                self.write_config(silent=True)
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
                self.write_config()
                return
            print('No user {}'.format(username))
