#!/usr/local/bin/python3
"""
Unit tests for linodecli.api_request
"""
import contextlib
import io
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from linodecli import api_request


class TestAPIRequest:
    """
    Unit tests for linodecli.api_request
    """

    def test_response_debug_info(self):
        stderr_buf = io.StringIO()

        mock_response = SimpleNamespace(
            raw=SimpleNamespace(version=11.1),
            status_code=200,
            reason="OK",
            headers={"cool": "test"},
        )

        with contextlib.redirect_stderr(stderr_buf):
            api_request._print_response_debug_info(mock_response)

        output = stderr_buf.getvalue()
        assert "< HTTP/1.1 200 OK" in output
        assert "< cool: test" in output

    def test_request_debug_info(self):
        stderr_buf = io.StringIO()

        with contextlib.redirect_stderr(stderr_buf):
            api_request._print_request_debug_info(
                SimpleNamespace(__name__="get"),
                "https://definitely.linode.com/",
                {"cool": "test"},
                "cool body",
            )

        output = stderr_buf.getvalue()
        assert "> GET https://definitely.linode.com/" in output
        assert "> cool: test" in output
        assert "> Body:" in output
        assert ">   cool body" in output
        assert "> " in output

    def test_build_request_body(self, mock_cli, create_operation):
        create_operation.allowed_defaults = ["region", "engine"]
        create_operation.action = "mysql-create"
        result = api_request._build_request_body(
            mock_cli,
            create_operation,
            SimpleNamespace(generic_arg="foo", region=None, engine=None),
        )
        assert (
            json.dumps(
                {
                    "generic_arg": "foo",
                    "region": "us-southeast",
                    "engine": "mysql/8.0.26",
                }
            )
            == result
        )

    def test_build_request_url_get(self, mock_cli, list_operation):
        result = api_request._build_request_url(
            mock_cli, list_operation, SimpleNamespace()
        )

        assert "http://localhost/foo/bar?page=1&page_size=100" == result

    def test_build_request_url_post(self, mock_cli, create_operation):
        result = api_request._build_request_url(
            mock_cli, create_operation, SimpleNamespace()
        )

        assert "http://localhost/foo/bar" == result

    def test_build_filter_header(self, list_operation):
        result = api_request._build_filter_header(
            list_operation, SimpleNamespace(filterable_result="bar")
        )

        assert json.dumps({"filterable_result": "bar"}) == result

    def test_do_request_get(self, mock_cli, list_operation):
        mock_response = Mock(status_code=200, reason="OK")

        def validate_http_request(url, headers=None, data=None, **kwargs):
            assert url == "http://localhost/foo/bar?page=1&page_size=100"
            assert headers["X-Filter"] == json.dumps(
                {"filterable_result": "cool"}
            )
            assert "Authorization" in headers
            assert data is None

            return mock_response

        with patch("linodecli.api_request.requests.get", validate_http_request):
            result = api_request.do_request(
                mock_cli, list_operation, ["--filterable_result", "cool"]
            )

        print("NESTED:", list_operation.response_model.nested_list)

        assert result == mock_response

    def test_do_request_post(self, mock_cli, create_operation):
        mock_response = Mock(status_code=200, reason="OK")

        def validate_http_request(url, headers=None, data=None, **kwargs):
            assert url == "http://localhost/foo/bar"
            assert data == json.dumps(
                {
                    "test_param": 12345,
                    "generic_arg": "foobar",
                    "region": "us-southeast",  # default
                }
            )
            assert "Authorization" in headers

            return mock_response

        create_operation.allowed_defaults = ["region"]

        with patch(
            "linodecli.api_request.requests.post", validate_http_request
        ):
            result = api_request.do_request(
                mock_cli,
                create_operation,
                ["--generic_arg", "foobar", "--test_param", "12345"],
            )

        assert result == mock_response

    def test_outdated_cli(self, mock_cli):
        # "outdated" version
        mock_cli.suppress_warnings = False
        mock_cli.version = "1.0.0"
        mock_cli.spec_version = "1.0.0"

        # Return a mock response from PyPI
        def mock_http_response(url, headers=None, data=None, timeout=1):
            assert "pypi.org" in url

            r = requests.Response()
            r.status_code = 200

            def json_func():
                return {
                    "info": {
                        # Add a fake new version
                        "version": "1.1.0"
                    }
                }

            r.json = json_func
            return r

        stderr_buf = io.StringIO()

        # Provide a mock Linode API response
        mock_response = SimpleNamespace(
            status_code=200, reason="OK", headers={"X-Spec-Version": "1.1.0"}
        )

        with contextlib.redirect_stderr(stderr_buf), patch(
            "linodecli.api_request.requests.get", mock_http_response
        ):
            api_request._attempt_warn_old_version(mock_cli, mock_response)

        output = stderr_buf.getvalue()
        assert (
            "The API responded with version 1.1.0, which is newer than "
            "the CLI's version of 1.0.0.  Please update the CLI to get "
            "access to the newest features.  You can update with a "
            "simple `pip3 install --upgrade linode-cli`" in output
        )

    def test_outdated_cli_no_new_version(self, mock_cli):
        # "outdated" version
        mock_cli.suppress_warnings = False
        mock_cli.version = "1.0.0"
        mock_cli.spec_version = "1.0.0"

        # Return a mock response from PyPI
        def mock_http_response(url, headers=None, data=None, timeout=1):
            assert "pypi.org" in url

            r = requests.Response()
            r.status_code = 200

            def json_func():
                return {
                    "info": {
                        # No new CLI release :(
                        "version": "1.0.0"
                    }
                }

            r.json = json_func
            return r

        stderr_buf = io.StringIO()

        # Provide a mock Linode API response
        mock_response = SimpleNamespace(
            status_code=200, reason="OK", headers={"X-Spec-Version": "1.1.0"}
        )

        with contextlib.redirect_stderr(stderr_buf), patch(
            "linodecli.api_request.requests.get", mock_http_response
        ):
            api_request._attempt_warn_old_version(mock_cli, mock_response)

        output = stderr_buf.getvalue()
        assert "" == output

    def test_up_to_date_cli(self, mock_cli):
        # "up to date" version
        mock_cli.suppress_warnings = False
        mock_cli.version = "1.0.0"
        mock_cli.spec_version = "1.0.0"

        # Return a mock response from PyPI
        def mock_http_response(url, headers=None, data=None, timeout=1):
            assert "pypi.org" in url

            r = requests.Response()
            r.status_code = 200

            def json_func():
                return {"info": {"version": "1.0.0"}}

            r.json = json_func
            return r

        stderr_buf = io.StringIO()

        # Provide a mock Linode API response
        mock_response = SimpleNamespace(
            status_code=200, reason="OK", headers={"X-Spec-Version": "1.0.0"}
        )

        with contextlib.redirect_stderr(stderr_buf), patch(
            "linodecli.api_request.requests.get", mock_http_response
        ):
            api_request._attempt_warn_old_version(mock_cli, mock_response)

        output = stderr_buf.getvalue()
        assert "" == output
