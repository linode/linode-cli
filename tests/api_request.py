#!/usr/local/bin/python3
"""
Unit tests for linodecli.api_request
"""
import argparse
import contextlib
import io
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch, Mock

import requests

from linodecli import api_request
from tests.populators import make_test_cli, make_test_operation, make_test_create_operation, make_test_list_operation


class APIRequestTests(unittest.TestCase):
    """
    Unit tests for linodecli.api_request
    """

    def test_response_debug_info(self):
        stderr_buf = io.StringIO()

        mock_response = SimpleNamespace(
            raw=SimpleNamespace(version=11.1),
            status_code=200,
            reason="OK",
            headers={
                "cool": "test"
            }
        )

        with contextlib.redirect_stderr(stderr_buf):
            api_request._print_response_debug_info(mock_response)

        output = stderr_buf.getvalue()
        self.assertIn("< HTTP/1.1 200 OK", output)
        self.assertIn("< cool: test", output)


    def test_request_debug_info(self):
        stderr_buf = io.StringIO()

        with contextlib.redirect_stderr(stderr_buf):
            api_request._print_request_debug_info(
                SimpleNamespace(__name__="get"),
                "https://definitely.linode.com/",
                {
                    "cool": "test"
                },
                "cool body"
            )

        output = stderr_buf.getvalue()
        self.assertIn("> GET https://definitely.linode.com/", output)
        self.assertIn("> cool: test", output)
        self.assertIn("> Body:", output)
        self.assertIn(">   cool body", output)
        self.assertIn("> ", output)


    def test_build_request_body(self):
        operation = make_test_create_operation()
        operation.allowed_defaults = ["region"]

        result = api_request._build_request_body(
            make_test_cli(),
            operation,
            SimpleNamespace(generic_arg="foo", region=None)
        )

        self.assertEqual(
            json.dumps({"generic_arg": "foo", "region": "us-southeast"}),
            result
        )


    def test_build_request_url_get(self):
        result = api_request._build_request_url(
            make_test_cli(),
            make_test_list_operation(),
            SimpleNamespace()
        )

        self.assertEqual(
            "http://localhost/foo/bar?page=1&page_size=100",
            result
        )

    def test_build_request_url_post(self):
        result = api_request._build_request_url(
            make_test_cli(),
            make_test_create_operation(),
            SimpleNamespace()
        )

        self.assertEqual(
            "http://localhost/foo/bar",
            result
        )

    def test_build_filter_header(self):
        result = api_request._build_filter_header(
            make_test_list_operation(),
            SimpleNamespace(filterable_result="bar")
        )

        self.assertEqual(
            json.dumps({"filterable_result": "bar"}),
            result
        )

    @patch('linodecli.api_request.requests.get')
    def test_do_request_get(self, mock_get):
        cli = make_test_cli()

        mock_response = Mock(status_code=200, reason="OK")

        def validate_http_request(url, headers=None, data=None):
            self.assertEqual(url, "http://localhost/foo/bar?page=1&page_size=100")
            self.assertEqual(headers["X-Filter"], json.dumps({
                "filterable_result": "cool"
            }))
            self.assertIn("Authorization", headers)
            self.assertIsNone(data)

            return mock_response

        mock_get.side_effect = validate_http_request

        result = api_request.do_request(
            cli,
            make_test_list_operation(),
            ["--filterable_result", "cool"]
        )

        self.assertEqual(result, mock_response)

    @patch('linodecli.api_request.requests.post')
    def test_do_request_post(self, mock_get):
        cli = make_test_cli()

        mock_response = Mock(status_code=200, reason="OK")

        def validate_http_request(url, headers=None, data=None):
            self.assertEqual(url, "http://localhost/foo/bar")
            self.assertEqual(
                data,
                json.dumps({
                    "test_param": 12345,
                    "generic_arg": "foobar",
                    "region": "us-southeast" # default
                })
            )
            self.assertIn("Authorization", headers)

            return mock_response

        mock_get.side_effect = validate_http_request

        operation = make_test_create_operation()
        operation.allowed_defaults = ["region"]

        result = api_request.do_request(
            cli,
            operation,
            ["--generic_arg", "foobar", "12345"]
        )

        self.assertEqual(result, mock_response)