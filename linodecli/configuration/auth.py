"""
Helper functions for configuration related to auth
"""

import re
import socket
import sys
import webbrowser
from http import server
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import requests

from linodecli.exit_codes import ExitCodes
from linodecli.helpers import API_CA_PATH

TOKEN_GENERATION_URL = "https://cloud.linode.com/profile/tokens"

# The hardcoded OAuth client ID for use in web authentication.
# This client object exists under an official Linode account.
OAUTH_CLIENT_ID = "5823b4627e45411d18e9"

# In the event that we can't load the styled landing page from file, this will
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
    response: requests.Response,
    exit_on_error: bool = False,
    status_validator: Optional[Callable[[int], bool]] = None,
):
    """
    Handle the response status code and handle errors if necessary.

    :param response: The response object from the API call.
    :type response: requests.Response
    :param exit_on_error: If true, the CLI should exit if the response contains an error.
                          Defaults to False.
    :type exit_on_error: bool
    :param status_validator: A custom response validator function to run before
                             the default validation.
    :type status_validator: Optional[Callable[int], bool]
    """

    if status_validator is not None and status_validator(response.status_code):
        return

    if 199 < response.status_code < 300:
        return

    print(
        f"Could not contact {response.url} - Error: {response.status_code}",
        file=sys.stderr,
    )
    if exit_on_error:
        sys.exit(ExitCodes.REQUEST_FAILED)


# TODO: merge config do_request and cli do_request
def _do_get_request(
    base_url: str,
    path: str,
    token: Optional[str] = None,
    exit_on_error: bool = True,
    status_validator: Optional[Callable[[int], bool]] = None,
) -> Dict[str, Any]:
    """
    Runs an HTTP GET request.

    :param base_url: The base URL of the API.
    :type base_url: str
    :param path: The path of the API endpoint.
    :type path: str
    :param token: The authentication token to be used for this request.
    :type token: Optional[str]
    :param exit_on_error: If true, the CLI should exit if the response contains an error.
                          Defaults to False.
    :type exit_on_error: bool
    :param status_validator: A custom response validator function to run
                             before the default validation.
    :type status_validator: Optional[Callable[int], bool]

    :returns: The response from the API request.
    :rtype: Dict[str, Any]
    """
    return _do_request(
        base_url,
        requests.get,
        path,
        token=token,
        exit_on_error=exit_on_error,
        status_validator=status_validator,
    )


def _do_request(
    base_url: str,
    method: Callable,
    path: str,
    token: Optional[str] = None,
    exit_on_error: bool = False,
    body: Optional[Dict[str, Any]] = None,
    status_validator: Optional[Callable[[int], bool]] = None,
):  # pylint: disable=too-many-arguments
    """
    Runs an HTTP request.

    :param base_url: The base URL of the API.
    :type base_url: str
    :param method: The request method function to use.
    :type method: Callable
    :param path: The path of the API endpoint.
    :type path: str
    :param token: The authentication token to be used for this request.
    :type token: Optional[str]
    :param exit_on_error: If true, the CLI should exit if the response contains an error.
                          Defaults to False.
    :type exit_on_error: bool
    :param body: The body of this request.
    :type body: Optional[Dict[str, Any]]
    :param status_validator: A custom response validator function to run before
                             the default validation.
    :type status_validator: Optional[Callable[int], bool]

    :returns: The response body as a JSON object.
    :rtype: Dict[str, Any]
    """
    headers = {}

    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
        headers["Content-type"] = "application/json"

    result = method(
        base_url + path, headers=headers, json=body, verify=API_CA_PATH
    )

    _handle_response_status(
        result, exit_on_error=exit_on_error, status_validator=status_validator
    )

    return result.json()


def _check_full_access(base_url: str, token: str) -> bool:
    """
    Checks whether the given token has full-access permissions.

    :param base_url: The base URL for the API.
    :type base_url: str
    :param token: The access token to use.
    :type token :str

    :returns: Whether the user has full access.
    :rtype: bool
    """
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


def _username_for_token(base_url: str, token: str) -> str:
    """
    A helper function that returns the username associated with a token by
    requesting it from the API.

    :param base_url: The base URL for the API.
    :type base_url: str
    :param token: The access token to use.
    :type token :str

    :returns: The username for this token.
    :rtype: str
    """
    u = _do_get_request(base_url, "/profile", token=token, exit_on_error=False)
    if "errors" in u:
        reasons = ",".join([c["reason"] for c in u["errors"]])
        print(f"That token didn't work: {reasons}", file=sys.stderr)
        return None

    return u["username"]


def _get_token_terminal(base_url: str) -> Tuple[str, str]:
    """
    Handles prompting the user for a Personal Access Token and checking it
    to ensure it works.

    :param base_url: The base URL for the API.
    :type base_url: str

    :returns: A tuple containing the user's username and token.
    :rtype: Tuple[str, str]
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


def _get_token_web(base_url: str) -> Tuple[str, str]:
    """
    Generates a token using OAuth/web authentication..

    :param base_url: The base URL of the API.
    :type base_url: str

    :return: A tuple containing the username and web token.
    :rtype: Tuple[str, str]
    """
    temp_token = _handle_oauth_callback()
    username = _username_for_token(base_url, temp_token)

    if username is None:
        print(
            "OAuth failed.  Please try again of use a token for auth.",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.OAUTH_ERROR)

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


def _handle_oauth_callback() -> str:
    """
    Sends the user to a URL to perform an OAuth login for the CLI, then redirects
    them to a locally-hosted page that captures the token.

    :returns: The temporary OAuth token.
    :rtype: str
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
        print(
            "\nGiving up.  If you couldn't get web authentication to work, please "
            "try token using a token by invoking with `linode-cli configure --token`, "
            "and open an issue at https://github.com/linode/linode-cli",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.OAUTH_ERROR)

    return serv.token
