"""
Responsible for managing spec and routing commands to operations.
"""
from __future__ import print_function

from distutils.version import StrictVersion, LooseVersion
import json
import os
import pickle
from string import Template
from sys import exit, prefix, stderr, version_info

import requests

from .operation import CLIArg, CLIOperation, URLParam
from .response import ModelAttr, ResponseModel
from .configuration import CLIConfig
from .output import OutputHandler, OutputMode


METHODS = ('get','post','put','delete')


class CLI:
    """
    Responsible for loading or baking a spec and handling incoming commands
    """
    def __init__(self, version, base_url, skip_config=False, as_user=None):
        self.ops = {}
        self.spec = {}
        self.defaults = True # whether to use default values for arguments
        self.page = 1
        self.debug_request = False
        self.version = version
        self.base_url = base_url
        self.spec_version = 'None'
        self.suppress_warnings = False

        self.output_handler = OutputHandler()
        self.config = CLIConfig(self.base_url, skip_config=skip_config)
        self.load_baked()

    def _resolve_allOf(self, node):
        """
        Given the contents of an "allOf" node, returns the entire dct having parsed
        all refs and combined all other nodes.

        :param node: The contents of an 'allOf'
        :type node: list
        """
        ret = {}

        for cur in node:
            data = cur
            if '$ref' in cur:
                data = self._resolve_ref(cur['$ref'])
            props = {}
            if 'properties' in data:
                props = data['properties']
            elif '$ref' in cur and '/properties/' in cur['$ref']:
                # if we referenced a property, we got a property
                props = data
            else:
                print("Warning: Resolved empty node for {} in {}".format(cur, node))
            ret.update(props)
        return ret


    def _resolve_ref(self, ref):
        """
        Resolves a reference to the referenced component.

        :param ref: A reference path, like '#/components/schemas/Linode'
        :type ref: str

        :returns: The resolved reference
        :rtype: dct
        """
        path_parts = ref.split('/')[1:]
        tmp = self.spec
        for part in path_parts:
            tmp = tmp[part]

        return tmp

    def _parse_args(self, node, prefix=[], args=None):
        """
        Given a node in a requestBody, parses out the properties and returns the
        CLIArg info
        """
        if args is None:
            args = {}

        for arg, info in node.items():
            if 'allOf' in info:
                info = self._resolve_allOf(info['allOf'])
            if '$ref' in info:
                info = self._resolve_ref(info['$ref'])
            if 'properties' in info:
                self._parse_args(info['properties'], prefix=prefix+[arg], args=args)
                continue # we can't edit this level of the tree
            if info.get('readOnly'):
                continue
            path = '.'.join(prefix+[arg])
            args[path] = {
                "type": info.get('type') or 'string',
                "desc": info.get('description') or '',
                "name": arg,
                "format": info.get('x-linode-cli-format', info.get('format', None)),
            }

            # if this is coming in as json, stop here
            if args[path]["format"] == "json":
                args[path]["type"] = "object"
                continue

            # handle input lists
            if args[path]['type'] == 'array' and 'items' in info:
                items = info['items']

                if 'allOf' in items:
                    # if items contain an "allOf", parse it down and format it
                    # as is expected here
                    items = self._resolve_allOf(items['allOf'])
                    items = {"type":"object","items":items}
                if '$ref' in items:
                    # if it's just a ref, parse that out too
                    items = self._resolve_ref(items['$ref'])

                args[path]['item_type'] = items['type']

                if (items['type'] == 'object' and 'properties' in items and
                        not items.get('readOnly')):
                    # this is a special case - each item has its own properties
                    # that we need to capture separately
                    item_args = self._parse_args(items['properties'], prefix=prefix+[arg])
                    for _, v in item_args.items():
                        v['list_item'] = path
                    args.update(item_args)
                    del args[path] # remove the base element, which is junk

        return args

    def _parse_properties(self, node, prefix=[]):
        """
        Given the value of a "properties" node, parses out the attributes and
        returns them as a list
        """
        attrs = []
        for name, info in node.items():
            if 'properties' in info:
                attrs += self._parse_properties(info['properties'],
                                                prefix+[name])
            else:
                item_type = None
                item_container = info.get('items')
                if item_container:
                    item_type = item_container.get('type')
                attrs.append(ModelAttr(
                    '.'.join(prefix+[name]),
                    info.get('x-linode-filterable') or False,
                    info.get('x-linode-cli-display') or False,
                    info.get('type') or 'string',
                    color_map=info.get('x-linode-cli-color'),
                    item_type=item_type))

        return attrs

    def bake(self, spec):
        """
        Generates ops and bakes them to a pickle
        """
        self.spec = spec
        self.ops = {}
        default_servers = [c['url'] for c in spec['servers']]

        for path, data in self.spec['paths'].items():
            command = data.get("x-linode-cli-command") or "default"
            if command not in self.ops:
                self.ops[command] = {}

            params = []
            if 'parameters' in data:
                for info in data['parameters']:
                    if '$ref' in info:
                        info = self._resolve_ref(info['$ref'])
                    params.append(URLParam(info['name'], info['schema']['type']))
            for m in METHODS:
                if m in data:
                    if data[m].get('x-linode-cli-skip'):
                        # some actions aren't available to the CLI - skip them
                        continue

                    action = data[m].get('x-linode-cli-action') or data[m].get('operationId')

                    if action is None:
                        print("warn: no operationId for {} {}".format(m.upper(), path))
                        continue

                    summary = data[m].get('summary') or ''

                    use_servers = ([c['url'] for c in data[m]['servers']]
                                   if 'servers' in data[m] else default_servers)

                    args = {}
                    required_fields = []
                    if m in ('post','put') and 'requestBody' in data[m]:
                        if 'application/json' in data[m]['requestBody']['content']:
                            body_schema = data[m]['requestBody']['content']['application/json']['schema']

                            if 'required' in body_schema:
                                required_fields = body_schema['required']

                            if 'allOf' in body_schema:
                                body_schema = self._resolve_allOf(body_schema['allOf'])
                            if 'required' in body_schema:
                                required_fields += body_schema['required']
                            if '$ref' in body_schema:
                                body_schema = self._resolve_ref(body_schema['$ref'])
                            if 'required' in body_schema:
                                required_fields += body_schema['required']
                            if 'properties' in body_schema:
                                body_schema = body_schema['properties']
                            if 'required' in body_schema:
                                required_fields += body_schema['required']

                            args = self._parse_args(body_schema, args={})

                    response_model = None
                    if ('200' in data[m]['responses'] and
                        'application/json' in data[m]['responses']['200']['content']):
                        resp_con = data[m]['responses']['200']['content']['application/json']['schema']

                        if 'x-linode-cli-use-schema' in data[m]['responses']['200']['content']['application/json']:
                            # this body is atypical, and defines its own columns
                            # using this schema instead of the normal one.  This
                            # is usually pairs with x-linode-cli-rows so to handle
                            # endpoints that returns irregularly formatted data
                            resp_con = data[m]['responses']['200']['content']['application/json']['x-linode-cli-use-schema']

                        if '$ref' in resp_con:
                            resp_con = self._resolve_ref(resp_con['$ref'])
                        if 'allOf' in resp_con:
                            resp_con.update(self._resolve_allOf(resp_con['allOf']))
                        # handle pagination envelope
                        if 'properties' in resp_con and 'pages' in resp_con['properties']:
                            resp_con = resp_con['properties']
                        if 'pages' in resp_con and 'data' in resp_con:
                            if '$ref' in resp_con['data']['items']:
                                resp_con = self._resolve_ref(resp_con['data']['items']['$ref'])
                            else:
                                resp_con = resp_con['data']['items']

                        attrs = []
                        if 'properties' in resp_con:
                            attrs = self._parse_properties(resp_con['properties'])
                            # maybe we have special columns?
                            rows = data[m]['responses']['200']['content']['application/json'].get('x-linode-cli-rows') or None
                            nested_list = data[m]['responses']['200']['content']['application/json'].get('x-linode-cli-nested-list') or None
                            response_model = ResponseModel(attrs, rows=rows, nested_list=nested_list)

                    cli_args = []

                    for arg, info in args.items():
                        new_arg = CLIArg(info['name'], info['type'], info['desc'].split('.')[0]+'.',
                                         arg, info['format'], list_item=info.get('list_item'))

                        if arg in required_fields:
                            new_arg.required = True

                        # handle arrays
                        if 'item_type' in info:
                            new_arg.arg_item_type = info['item_type']
                        cli_args.append(new_arg)

                    # looks for param names that will be obscured by args
                    use_params = params[:]
                    use_path = path
                    for p in use_params:
                        if p.name in args.keys():
                            # if we found a parameter name that is also and argument name
                            # append an underscore to both the parameter name and the
                            # parameter name in the URL
                            use_path = use_path.replace("{"+p.name+"}", "{"+p.name+"_}")
                            p.name += '_'

                    self.ops[command][action] = CLIOperation(m, use_path, summary,
                                                             cli_args, response_model,
                                                             use_params, use_servers)

        # hide the base_url from the spec away
        self.ops['_base_url'] = spec['servers'][0]['url']
        self.ops['_spec_version'] = spec['info']['version']

        # finish the baking
        data_file = self._get_data_file()
        with open(data_file, 'wb') as f:
            pickle.dump(self.ops, f)

    def get_completions(self):
        """
        Generates and returns shell completions based on the baked spec
        """
        completion_template=Template("""# This is a generated file!  Do not modify!
_linode_cli()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    case "${prev}" in
        linode-cli)
            COMPREPLY=( $(compgen -W "$actions --help" -- ${cur}) )
            return 0
            ;;
        $command_items
        *)
            ;;
    esac
}

complete -F _linode_cli linode-cli""")

        command_template=Template("""$command)
            COMPREPLY=( $(compgen -W "$actions --help" -- ${cur}) )
            return 0
            ;;""")

        command_blocks = [command_template.safe_substitute(command=op, actions=" ".join([act for act in actions.keys()])) for op, actions in self.ops.items()]
        rendered = completion_template.safe_substitute(actions=" ".join(self.ops.keys()),
                                                       command_items="\n        ".join(command_blocks))
        return rendered

    def bake_completions(self):
        """
        Given a baked CLI, generates and saves a bash completion file
        """
        rendered = self.get_completions()
        # save it off
        with open('linode-cli.sh', 'w') as f:
            print("Writing file...")
            f.write(rendered)


    def load_baked(self):
        """
        Loads a baked spec representation from a baked pickle
        """
        data_file = self._get_data_file()
        data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),data_file)
        if os.path.exists(data_path):
            with open(data_path, 'rb') as f:
                self.ops = pickle.load(f)
                if '_base_url' in self.ops:
                    self.base_url = self.ops['_base_url']
                    del self.ops['_base_url']
                if '_spec_version' in self.ops:
                    self.spec_version = self.ops['_spec_version']
                    del self.ops['_spec_version']
        else:
            print("No spec baked.  Please bake by calling this script as follows:")
            print("  python3 gen_cli.py bake /path/to/spec")
            self.ops = None # this signals __init__.py to give up

    def _get_data_file(self):
        """
        Returns the name of the baked data file this program wants.  This is in
        part based on python version.
        """
        return 'data-{}'.format(version_info[0])

    def print_request_debug_info(self, method, url, headers, body):
        """
        Prints debug info for an HTTP request
        """
        print('> {} {}'.format(method.__name__.upper(), url), file=stderr)
        for k, v in headers.items():
            print('> {}: {}'.format(k, v), file=stderr)
        print("> Body:", file=stderr)
        print(">  ", body or "", file=stderr)
        print("> ", file=stderr)

    def print_response_debug_info(self, response):
        """
        Prints debug info for a response from requests
        """
        # these come back as ints, convert to HTTP version
        http_version = response.raw.version/10

        print('< HTTP/{:.1f} {} {}'.format(http_version, response.status_code, response.reason), file=stderr)
        for k, v in response.headers.items():
            print('< {}: {}'.format(k, v), file=stderr)
        print('< ', file=stderr)

    def do_request(self, operation, args, filter_header=None, skip_error_handling=False):
        """
        Makes a request to an operation's URL and returns the resulting JSON, or
        prints and error if a non-200 comes back
        """
        method = getattr(requests, operation.method)
        headers = {
            'Authorization': "Bearer {}".format(self.config.get_token()),
            'Content-Type': 'application/json',
            'User-Agent': "linode-cli:{} python/{}.{}.{}".format(self.version, version_info[0], version_info[1], version_info[2]),
        }

        parsed_args = operation.parse_args(args)

        url = operation.url.format(**vars(parsed_args))

        if operation.method == 'get':
            url+='?page={}'.format(self.page)

        body = None
        if operation.method == 'get':
            if filter_header is not None:
                # plugins can specify their own filters - use those by default
                headers["X-Filter"] = json.dumps(filter_header)
            else:
                # otherwise, get filters from the CLI call
                filters = vars(parsed_args)
                # remove URL parameters
                for p in operation.params:
                    if p.name in filters:
                        del filters[p.name]
                # remove empty filters
                filters = {k: v for k, v in filters.items() if v is not None}
                # apply filter, if any
                if filters:
                    headers["X-Filter"] = json.dumps(filters)
        else:
            if self.defaults:
                parsed_args = self.config.update(parsed_args)

            to_json = {k: v for k, v in vars(parsed_args).items() if v is not None}

            expanded_json = {}
            # expand paths
            for k, v in to_json.items():
                cur = expanded_json
                for part in k.split('.')[:-1]:
                    if part not in cur:
                        cur[part] = {}
                    cur = cur[part]
                cur[k.split('.')[-1]] = v

            body = json.dumps(expanded_json)

        if self.debug_request:
            self.print_request_debug_info(method, url, headers, body)

        result =  method(url, headers=headers, data=body)

        if self.debug_request:
            self.print_response_debug_info(result)

        if not self.suppress_warnings:
            # check the major/minor version API reported against what we were built
            # with to see if an upgrade should be available
            api_version_higher = False

            if 'X-Spec-Version' in result.headers:
                spec_version = result.headers.get('X-Spec-Version')

                try:
                    # Parse the spec versions from the API and local CLI.
                    StrictVersion(spec_version)
                    StrictVersion(self.spec_version)

                    # Get only the Major/Minor version of the API Spec and CLI Spec, ignore patch version differences
                    spec_major_minor_version = spec_version.split(".")[0] + "." + spec_version.split(".")[1]
                    current_major_minor_version = self.spec_version.split(".")[0] + "." + self.spec_version.split(".")[1]
                except ValueError:
                    # If versions are non-standard like, "DEVELOPMENT" use them and don't complain.
                    spec_major_minor_version = spec_version
                    current_major_minor_version = self.spec_version

                try:
                    if LooseVersion(spec_major_minor_version) > LooseVersion(current_major_minor_version):
                        api_version_higher = True
                except:
                    # if this comparison or parsing failed, still process output
                    print("Parsing failed when comparing local version {} with server "
                          "version {}.  If this problem persists, please open a ticket "
                          "with `linode-cli support ticket-create`".format(
                             self.spec_version, spec_version
                          ), file=stderr)

            if api_version_higher:
                # check to see if there is, in fact, a version to upgrade to.  If not, don't
                # suggest an upgrade (since there's no package anyway)
                new_version_exists = False

                try:
                    # do this all in a try block since it must _never_ prevent the CLI
                    # from showing command output
                    pypi_response = requests.get(
                        'https://pypi.org/pypi/linode-cli/json',
                         timeout=1 # seconds
                    )

                    if pypi_response.status_code == 200:
                        # we got data back
                        pypi_version = pypi_response.json()['info']['version']

                        # no need to be fancy; these should always be valid versions
                        if LooseVersion(pypi_version) > LooseVersion(self.version):
                            new_version_exists = True
                except:
                    # I know, but if anything happens here the end user should still
                    # be able to see the command output
                    print("Unable to determine if a new linode-cli package is available "
                          "in pypi.  If this message persists, open a ticket or invoke "
                          "with --suppress-warnings",
                          file=stderr)
                    pass

                if new_version_exists:
                    print("The API responded with version {}, which is newer than "
                          "the CLI's version of {}.  Please update the CLI to get "
                          "access to the newest features.  You can update with a "
                          "simple `pip install --upgrade linode-cli`".format(
                              spec_version, self.spec_version
                          ), file=stderr)

        if not 199 < result.status_code < 399 and not skip_error_handling:
            self._handle_error(result)

        return result

    def _handle_error(self, response):
        """
        Given an error message, properly displays the error to the user and exits.
        """
        print("Request failed: {}".format(response.status_code), file=stderr)

        resp_json = response.json()

        if 'errors' in resp_json:
            data = [[error.get('field') or '', error.get('reason')] for error in resp_json['errors']]
            self.output_handler.print(None, data, title='errors', to=stderr,
                                      columns=['field','reason'])
        exit(1)

    def handle_command(self, command, action, args):
        """
        Given a command, action, and remaining kwargs, finds and executes the
        action
        """
        if command not in self.ops:
            print("Command not found: {}".format(command))
            exit(1)
        elif action not in self.ops[command]:
            print("No action {} for command {}".format(action, command))
            exit(1)

        operation = self.ops[command][action]

        result = self.do_request(operation, args)

        operation.process_response_json(result.json(), self.output_handler)

        if (self.output_handler.mode == OutputMode.table and 'pages' in result.json()
            and result.json()['pages'] > 1):
            print('Page {} of {}.  Call with --page [PAGE] to load a different page.'.format(
                result.json()['page'], result.json()['pages']))

    def configure(self):
        """
        Reconfigure the application
        """
        self.config.configure()

    def call_operation(self, command, action, args=[], filters=None):
        """
        This function is used in plugins to retrieve the result of CLI operations
        in JSON format.  This uses the configured user of the CLI.

        :param filters: The X-Filter header to include in the request.  This overrides
                        whatever is passed into to command as filters.
        :type filters: dict
        """
        if command not in self.ops or action not in self.ops[command]:
            raise ValueError('Unknown command/action {}/{}'.format(command, action))

        operation = self.ops[command][action]

        result = self.do_request(operation, args, filter_header=filters, skip_error_handling=True)

        return result.status_code, result.json()
