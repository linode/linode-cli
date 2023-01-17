def _handle_oauth_callback(self):
    """
    Sends the user to a URL to perform an OAuth login for the CLI, then redirets
    them to a locally-hosted page that captures teh token
    """
    # load up landing page HTML
    landing_page_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "oauth-landing-page.html"
    )

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
                    landing_page.format(port=self.server.server_address[1]).encode(
                        "utf-8"
                    )
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
