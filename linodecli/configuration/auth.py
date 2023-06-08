"""
Helper functions for configuration related to auth
"""

import re
import socket
import sys
import webbrowser
from http import server
from pathlib import Path

import requests

from linodecli.helpers import API_CA_PATH

TOKEN_GENERATION_URL = "https://cloud.linode.com/profile/tokens"
# This is used for web-based configuration
OAUTH_CLIENT_ID = "5823b4627e45411d18e9"
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


def _handle_response_status(
    response, exit_on_error=None, status_validator=None
):
    if status_validator is not None and status_validator(response.status_code):
        return

    if 199 < response.status_code < 300:
        return

    print(f"Could not contact {response.url} - Error: {response.status_code}")
    if exit_on_error:
        sys.exit(4)


# TODO: merge config do_request and cli do_request
def _do_get_request(
    base_url, url, token=None, exit_on_error=True, status_validator=None
):
    """
    Does helper get requests during configuration
    """
    return _do_request(
        base_url,
        requests.get,
        url,
        token=token,
        exit_on_error=exit_on_error,
        status_validator=status_validator,
    )


def _do_request(
    base_url,
    method,
    url,
    token=None,
    exit_on_error=None,
    body=None,
    status_validator=None,
):  # pylint: disable=too-many-arguments
    """
    Does helper requests during configuration
    """
    headers = {}

    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
        headers["Content-type"] = "application/json"

    result = method(
        base_url + url, headers=headers, json=body, verify=API_CA_PATH
    )

    _handle_response_status(
        result, exit_on_error=exit_on_error, status_validator=status_validator
    )

    return result.json()


def _check_full_access(base_url, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    result = requests.get(
        base_url + "/profile/grants",
        headers=headers,
        timeout=120,
        verify=API_CA_PATH,
    )

    _handle_response_status(result, exit_on_error=True)

    return result.status_code == 204


def _username_for_token(base_url, token):
    """
    A helper function that returns the username associated with a token by
    requesting it from the API
    """
    u = _do_get_request(base_url, "/profile", token=token, exit_on_error=False)
    if "errors" in u:
        reasons = ",".join([c["reason"] for c in u["errors"]])
        print(f"That token didn't work: {reasons}")
        return None

    return u["username"]


def _get_token_terminal(base_url):
    """
    Handles prompting the user for a Personal Access Token and checking it
    to ensure it works.
    """
    print(
        f"""
First, we need a Personal Access Token.  To get one, please visit
{TOKEN_GENERATION_URL} and click
"Create a Personal Access Token".  The CLI needs access to everything
on your account to work correctly."""
    )

    while True:
        token = input("Personal Access Token: ")

        username = _username_for_token(base_url, token)
        if username is not None:
            break

    return username, token


def _get_token_web(base_url):
    """
    Handles OAuth authentication for the CLI.  This requires us to get a temporary
    token over OAuth and then use it to create a permanent token for the CLI.
    This function returns the token the CLI should use, or exits if anything
    goes wrong.
    """
    temp_token = _handle_oauth_callback()
    username = _username_for_token(base_url, temp_token)

    if username is None:
        print("OAuth failed.  Please try again of use a token for auth.")
        sys.exit(1)

    # the token returned via public oauth will expire in 2 hours, which
    # isn't great.  Instead, we're gonna make a token that expires never
    # and store that.
    result = _do_request(
        base_url,
        requests.post,
        "/profile/tokens",
        token=temp_token,
        # generate the actual token with a label like:
        #  Linode CLI @ linode
        # The creation date is already recoreded with the token, so
        # this should be all the relevant info.
        body={"label": f"Linode CLI @ {socket.gethostname()}"},
    )

    return username, result["token"]


def _handle_oauth_callback():
    """
    Sends the user to a URL to perform an OAuth login for the CLI, then redirets
    them to a locally-hosted page that captures teh token
    """
    # load up landing page HTML
    landing_page_path = Path(__file__).parent.parent / "oauth-landing-page.html"
    try:
        with open(landing_page_path, encoding="utf-8") as f:
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
            """
            get the access token
            """
            if "token" in self.path:
                # we got a token!  Parse it out of the request
                token_part = self.path.split("/", 2)[2]

                m = re.search(r"access_token=([a-z0-9]+)", token_part)
                if m and len(m.groups()):
                    self.server.token = m.groups()[0]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            # TODO: Clean up this page and make it look nice
            self.wfile.write(
                bytes(
                    landing_page.format(
                        port=self.server.server_address[1]
                    ).encode("utf-8")
                )
            )

        def log_message(self, form, *args):  # pylint: disable=arguments-differ
            """Don't actually log the request"""

    # start a server to catch the response
    serv = server.HTTPServer(("localhost", 0), Handler)
    serv.token = None

    # figure out the URL to direct the user to and print out the prompt
    # pylint: disable-next=line-too-long
    url = f"https://login.linode.com/oauth/authorize?client_id={OAUTH_CLIENT_ID}&response_type=token&scopes=*&redirect_uri=http://localhost:{serv.server_address[1]}"
    print(
        f"""A browser should open directing you to this URL to authenticate:

{url}

If you are not automatically directed there, please copy/paste the link into your browser
to continue..
"""
    )

    webbrowser.open(url)

    try:
        while serv.token is None:
            # serve requests one at a time until we get a token or are interrupted
            serv.handle_request()
    except KeyboardInterrupt:
        print()
        print(
            "Giving up.  If you couldn't get web authentication to work, please "
            "try token using a token by invoking with `linode-cli configure --token`, "
            "and open an issue at https://github.com/linode/linode-cli"
        )
        sys.exit(1)

    return serv.token
