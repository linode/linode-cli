"""
This module is responsible for handling HTTP requests to the Linode API.
"""

import itertools
import json
import sys
import time
from sys import version_info
from typing import Iterable, List, Optional

import requests
from packaging import version
from requests import Response

from linodecli.helpers import API_CA_PATH

from .baked.operation import ExplicitNullValue, OpenAPIOperation
from .helpers import handle_url_overrides


def get_all_pages(ctx, operation: OpenAPIOperation, args: List[str]):
    """
    Receive all pages of a resource from multiple
    API responses then merge into one page.

    :param ctx: The main CLI object
    """

    ctx.page_size = 500
    ctx.page = 1
    result = do_request(ctx, operation, args).json()

    total_pages = result.get("pages")

    if total_pages and total_pages > 1:
        pages_needed = range(2, total_pages + 1)

        result = _merge_results_data(
            itertools.chain(
                (result,),
                _generate_all_pages_results(ctx, operation, args, pages_needed),
            )
        )
    return result


def do_request(
    ctx,
    operation,
    args,
    filter_header=None,
    skip_error_handling=False,
) -> (
    Response
):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """
    Makes a request to an operation's URL and returns the resulting JSON, or
    prints and error if a non-200 comes back

    :param ctx: The main CLI object
    """
    # TODO: Revisit using pre-built calls from OpenAPI
    method = getattr(requests, operation.method)
    headers = {
        "Authorization": f"Bearer {ctx.config.get_token()}",
        "Content-Type": "application/json",
        "User-Agent": (
            f"linode-cli:{ctx.version} "
            f"python/{version_info[0]}.{version_info[1]}.{version_info[2]}"
        ),
    }

    parsed_args = operation.parse_args(args)

    url = _build_request_url(ctx, operation, parsed_args)

    body = _build_request_body(ctx, operation, parsed_args)

    filter_header = _build_filter_header(
        operation, parsed_args, filter_header=filter_header
    )
    if filter_header is not None:
        headers["X-Filter"] = filter_header

    # Print response debug info is requested
    if ctx.debug_request:
        _print_request_debug_info(method, url, headers, body)

    result = method(url, headers=headers, data=body, verify=API_CA_PATH)

    # Print response debug info is requested
    if ctx.debug_request:
        _print_response_debug_info(result)

    while _check_retry(result) and not ctx.no_retry and ctx.retry_count < 3:
        time.sleep(_get_retry_after(result.headers))
        ctx.retry_count += 1
        result = method(url, headers=headers, data=body, verify=API_CA_PATH)

    _attempt_warn_old_version(ctx, result)

    if not 199 < result.status_code < 399 and not skip_error_handling:
        _handle_error(ctx, result)

    return result


def _merge_results_data(results: Iterable[dict]):
    """Merge multiple json response into one"""

    iterator = iter(results)
    merged_result = next(iterator, None)
    if not merged_result:
        return None

    if "pages" in merged_result:
        merged_result["pages"] = 1
    if "page" in merged_result:
        merged_result["page"] = 1
    if "data" in merged_result:
        merged_result["data"] += list(
            itertools.chain.from_iterable(r["data"] for r in iterator)
        )
    return merged_result


def _generate_all_pages_results(
    ctx,
    operation: OpenAPIOperation,
    args: List[str],
    pages_needed: Iterable[int],
):
    """
    :param ctx: The main CLI object
    """
    for p in pages_needed:
        ctx.page = p
        yield do_request(ctx, operation, args).json()


def _build_filter_header(
    operation, parsed_args, filter_header=None
) -> Optional[str]:
    if operation.method != "get":
        # Non-GET operations don't support filters
        return None

    if filter_header is not None:
        return json.dumps(filter_header)

    parsed_args_dict = vars(parsed_args)

    # remove URL parameters
    for p in operation.params:
        if p.name in parsed_args_dict:
            del parsed_args_dict[p.name]

    # check for order-by and order
    order_by = parsed_args_dict.pop("order_by")
    order = parsed_args_dict.pop("order") or "asc"

    # The "+and" list to be used in the filter header
    filter_list = []

    for k, v in parsed_args_dict.items():
        if v is None:
            continue

        # If this is a list, flatten it out
        new_filters = [{k: j} for j in v] if isinstance(v, list) else [{k: v}]
        filter_list.extend(new_filters)

    result = {}
    if len(filter_list) > 0:
        if len(filter_list) == 1:
            result = filter_list[0]
        else:
            result["+and"] = filter_list
    if order_by is not None:
        result["+order_by"] = order_by
        result["+order"] = order
    return json.dumps(result) if len(result) > 0 else None


def _build_request_url(ctx, operation, parsed_args) -> str:
    target_server = handle_url_overrides(
        operation.url_base,
        host=ctx.config.get_value("api_host"),
        version=ctx.config.get_value("api_version"),
        scheme=ctx.config.get_value("api_scheme"),
    )

    result = f"{target_server}{operation.url_path}".format(**vars(parsed_args))

    if operation.method == "get":
        result += f"?page={ctx.page}&page_size={ctx.page_size}"

    return result


def _build_request_body(ctx, operation, parsed_args) -> Optional[str]:
    if operation.method == "get":
        # Get operations don't have a body
        return None

    # Merge defaults into body if applicable
    if ctx.defaults:
        parsed_args = ctx.config.update(parsed_args, operation.allowed_defaults)

    to_json = {}

    for k, v in vars(parsed_args).items():
        # Skip null values
        if v is None:
            continue

        # Explicitly include ExplicitNullValues
        if isinstance(v, ExplicitNullValue):
            to_json[k] = None
            continue

        to_json[k] = v

    expanded_json = {}

    # expand paths
    for k, v in to_json.items():
        cur = expanded_json
        for part in k.split(".")[:-1]:
            if part not in cur:
                cur[part] = {}
            cur = cur[part]
        cur[k.split(".")[-1]] = v

    return json.dumps(expanded_json)


def _print_request_debug_info(method, url, headers, body):
    """
    Prints debug info for an HTTP request
    """
    print(f"> {method.__name__.upper()} {url}", file=sys.stderr)
    for k, v in headers.items():
        print(f"> {k}: {v}", file=sys.stderr)
    print("> Body:", file=sys.stderr)
    print(">  ", body or "", file=sys.stderr)
    print("> ", file=sys.stderr)


def _print_response_debug_info(response):
    """
    Prints debug info for a response from requests
    """
    # these come back as ints, convert to HTTP version
    http_version = response.raw.version / 10

    print(
        f"< HTTP/{http_version:.1f} {response.status_code} {response.reason}",
        file=sys.stderr,
    )
    for k, v in response.headers.items():
        print(f"< {k}: {v}", file=sys.stderr)
    print("< ", file=sys.stderr)


def _attempt_warn_old_version(ctx, result):
    if ctx.suppress_warnings:
        return

    api_version_higher = False

    if "X-Spec-Version" in result.headers:
        spec_version = result.headers.get("X-Spec-Version")

        try:
            # Parse the spec versions from the API and local CLI.
            spec_version_parsed = version.parse(spec_version)
            current_version_parsed = version.parse(ctx.spec_version)

            # Get only the Major/Minor version of the API Spec and CLI Spec,
            # ignore patch version differences
            spec_major_minor_version = (
                f"{spec_version_parsed.major}.{spec_version_parsed.minor}"
            )
            current_major_minor_version = (
                f"{current_version_parsed.major}.{current_version_parsed.minor}"
            )
        except ValueError:
            # If versions are non-standard like, "DEVELOPMENT" use them and don't complain.
            spec_major_minor_version = spec_version
            current_major_minor_version = ctx.spec_version

        try:
            if version.parse(spec_major_minor_version) > version.parse(
                current_major_minor_version
            ):
                api_version_higher = True
        except:
            # if this comparison or parsing failed, still process output
            print(
                f"Parsing failed when comparing local version {ctx.spec_version} with  "
                f"server version {spec_version}.  If this problem persists, please open a "
                "ticket with `linode-cli support ticket-create`",
                file=sys.stderr,
            )

    if api_version_higher:
        # check to see if there is, in fact, a version to upgrade to.  If not, don't
        # suggest an upgrade (since there's no package anyway)
        new_version_exists = False

        try:
            # do this all in a try block since it must _never_ prevent the CLI
            # from showing command output
            pypi_response = requests.get(
                "https://pypi.org/pypi/linode-cli/json", timeout=1  # seconds
            )

            if pypi_response.status_code == 200:
                # we got data back
                pypi_version = pypi_response.json()["info"]["version"]

                # no need to be fancy; these should always be valid versions
                if version.parse(pypi_version) > version.parse(ctx.version):
                    new_version_exists = True
        except:
            # I know, but if anything happens here the end user should still
            # be able to see the command output
            print(
                "Unable to determine if a new linode-cli package is available "
                "in pypi.  If this message persists, open a ticket or invoke "
                "with --suppress-warnings",
                file=sys.stderr,
            )

        if new_version_exists:
            print(
                f"The API responded with version {spec_version}, which is newer than "
                f"the CLI's version of {ctx.spec_version}.  Please update the CLI to get "
                "access to the newest features.  You can update with a "
                "simple `pip3 install --upgrade linode-cli`",
                file=sys.stderr,
            )


def _handle_error(ctx, response):
    """
    Given an error message, properly displays the error to the user and exits.
    """
    print(f"Request failed: {response.status_code}", file=sys.stderr)

    resp_json = response.json()

    if "errors" in resp_json:
        data = [
            [error.get("field") or "", error.get("reason")]
            for error in resp_json["errors"]
        ]
        ctx.output_handler.print(
            data,
            ["field", "reason"],
            title="errors",
            to=sys.stderr,
        )
    sys.exit(1)


def _check_retry(response):
    """
    Check for valid retry scenario, returns true if retry is valid
    """
    if response.status_code in (408, 429):
        # request timed out or rate limit exceeded
        return True

    return (
        response.headers
        and response.status_code == 400
        and response.headers.get("Server") == "nginx"
        and response.headers.get("Content-Type") == "text/html"
    )


def _get_retry_after(headers):
    retry_str = headers.get("Retry-After", "")
    return int(retry_str) if retry_str else 0
