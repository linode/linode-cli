# Baked Module Guide

## Core Constraint
- `linodecli/baked/` converts OpenAPI objects into a pickled runtime command model. The output is `data-3`, copied to `linodecli/data-3` by `make bake` and loaded at CLI startup.
- Constructors and bake helpers may read `openapi3` `Operation`, `MediaType`, `Schema`, and `Parameter` objects, but anything stored on `OpenAPIOperation`, `OpenAPIRequest`, `OpenAPIResponse`, `OpenAPIRequestArg`, `OpenAPIResponseAttr`, or `OpenAPIOperationParameter` must be pickle-safe for runtime loading.
- Do not store raw `openapi3` objects on baked models. Extract strings, numbers, booleans, lists, dicts, `None`, or simple project classes during bake.
- The `openapi3` library exposes spec extensions without the `x-` prefix. Code looks up keys like `linode-cli-use-schema`, `linode-cli-display`, and `linode-filterable`.
- If you change behavior or architecture described in this file, update this `AGENTS.md` in the same change.

## Bake And Runtime Flow
- `linodecli/cli.py:CLI.bake()` iterates spec paths and only `get/post/put/delete`, skips operations with `linode-cli-skip`, resolves command/action, constructs `OpenAPIOperation`, then pickles `self.ops`.
- `CLI._load_openapi_spec()` normalizes OpenAPI Parameter `content` forms into top-level `schema` before calling `openapi3.OpenAPI(...)`; keep this when changing spec loading because `openapi3` does not support parameter `content` directly.
- `OpenAPIOperation.__init__` coordinates bake-time extraction: response model, request/filter model, path parameters excluding `apiVersion`, URL components, docs URL, allowed defaults, action aliases, and CLI code samples.
- Runtime command execution does not parse OpenAPI. `OpenAPIOperation.parse_args()` builds argparse from baked attrs, `linodecli/api_request.py` builds URL/filter/body, and `OpenAPIOperation.process_response_json()` applies output overrides before `response_model.fix_json()` and `OutputHandler.print_response()`.
- `CLI.load_baked()` unpickles `linodecli/data-3`, pops metadata keys (`_base_url`, `_spec_version`, `_spec`) off the ops map, and stores them on the `CLI` instance (`base_url`, `spec_version`, `spec`). Do not assume those keys remain in the runtime command map.

## File Roles
- `operation.py`: main baked operation object, argparse actions, URL/docs resolution, response dispatch. Special user input sentinels live here: `ExplicitNullValue`, `ExplicitEmptyListValue`, `ExplicitJsonValue`.
- `request.py`: turns JSON request schemas into flat CLI args. Arrays of objects get both a parent JSON arg and child dot-path args.
- `response.py`: turns response schemas into output attrs and normalizes API JSON via `fix_json()`.
- `util.py`: composition/property aggregation plus dot-path escaping. Use `escape_arg_segment()` and `get_path_segments()` when schema property names can contain periods.
- `parsing.py`: short help-text extraction and Markdown-to-Rich conversion for baked descriptions.

## OpenAPI Extensions Used Here
- Path/operation routing: `linode-cli-command`, `linode-cli-action`, `linode-cli-skip`.
- RequestBody extension: `linode-cli-allowed-defaults` is read from `operation.requestBody.extensions`, not from the JSON schema or media-type schema.
- Request schema/media-type parsing: `linode-cli-format`, `linode-cli-use-schema`, `linode-cli-skip`.
- Response/output parsing: `linode-cli-display`, `linode-cli-color`, `linode-filterable`, `linode-cli-rows`, `linode-cli-nested-list`, `linode-cli-subtables`, `linode-cli-use-schema`, `linode-cli-skip`.
- Samples: operation extension `code-samples`; only entries whose `lang` lowercases to `cli` are stored.

## Request Parsing Gotchas
- `_aggregate_schema_properties()` merges `oneOf`, `anyOf`, and `allOf`; a field is marked required only if every leaf schema that defines properties requires it. Schemas that only nest composition without their own `properties` do not increment the required-count denominator.
- `OpenAPIRequest.attr_routes` stores per-`oneOf` option args keyed by schema `title`; oneOf entries without titles raise `ValueError`.
- `OpenAPIOperation.arg_routes` returns `self.request.attr_routes` (a dict) when a request exists, but `[]` when there is no request. Treat the empty case as a type inconsistency (list vs dict); callers that always call `.items()` will break on the no-request path.
- Request and response attributes marked `linode-cli-skip` are omitted from generated args/output.
- `linode-cli-use-schema` on `application/json` media types swaps the schema before parsing; this is used for CLI-specific request or display shapes.
- `linode-cli-format: json` stops deeper request parsing and accepts raw JSON. Deeply nested arrays are also treated as JSON.
- For arrays of objects, `_parse_request_model()` adds a parent arg that accepts JSON plus child args for each object property. `ListArgumentAction` groups adjacent child values into list items before `_build_request_body()` expands dot paths.
- Parent list args and child list args are mutually exclusive at runtime; `operation.py` validates conflicts such as `--interfaces` with `--interfaces.purpose`.
- `null` only becomes an explicit JSON null for nullable args. Unspecified `None` values are dropped later by `_traverse_request_body()` in `api_request.py`.
- `OptionalFromFileAction` loads file content only if the value resolves to an existing file; on Windows it also expands glob patterns before checking.
- `PasswordPromptAction` reads an explicit value, then `LINODE_CLI_<DEST>`, then prompts interactively.

## Request Body And Filters
- `api_request._build_request_body()` excludes path params, applies config defaults from `operation.allowed_defaults` when defaults are enabled, expands escaped dot-path keys with `get_path_segments()`, then serializes after `_traverse_request_body()`.
- `--raw-body` is only valid for POST/PUT-style body actions and cannot be combined with generated action args.
- GET filter args are generated only from paginated response attrs marked `linode-filterable`.
- `--order-by` is restricted to filterable attrs and becomes `+order_by` in `X-Filter`; list filters serialize as `+and` entries.

## Response And Output Gotchas
- Bake-time pagination detection is structural: top-level response schema must have exactly `pages`, `page`, `results`, and `data`; only `data.items` becomes display attrs (`is_paginated`).
- `OpenAPIResponse.fix_json()` handles `linode-cli-rows`, then `linode-cli-nested-list`, then unwraps via `"pages" in json` (not `self.is_paginated`), then wraps non-lists. Runtime unwrap is looser than bake-time pagination; do not tighten it to `is_paginated` without checking odd payloads that only include `pages`.
- `linode-cli-rows` paths are extracted from the raw API JSON and concatenated; list values extend the result, scalar/object values are appended.
- `linode-cli-nested-list` flattens configured nested lists and adds `_split` with the final path segment.
- `linode-cli-subtables` is stored on the response model, but table splitting is implemented in `linodecli/output/output_handler.py`.
- `linode-cli-display` controls default columns and ordering; if no columns are selected or displayed, `OutputHandler` falls back to all attrs.
- `linode-cli-color` rendering expects a `default_` color for values not present in the map.
- Response attrs keep full dot-path names for lookup. `OutputHandler` deep-copies attrs before subtable scoping because it mutates attr names and nesting depth while printing.
- JSON output intentionally ignores nested-list depth filtering so nested data can be displayed correctly.

## URL And Docs
- `_get_api_url_components()` uses the operation server or root server, resolves the default API version from server path or the `apiVersion` path parameter, and inserts `/{apiVersion}` when the path lacks it.
- Runtime URL overrides and pagination query params are applied in `api_request._build_request_url()`, not during bake. API version can come from `LINODE_CLI_API_VERSION`, config `api_version`, or the baked default.
- Docs URLs prefer `operation.externalDocs.url`; legacy fallback derives a Linode docs anchor from the first tag and summary.

## Tests
- Unit tests for this module use minimal OpenAPI fixtures under `tests/fixtures/` and fixtures in `tests/unit/conftest.py` that construct real `OpenAPIOperation` objects.
- For bake/request/response changes, add or update a fixture plus focused tests in `tests/unit/test_operation.py`, `test_request.py`, `test_response.py`, `test_api_request.py`, or `test_output.py` as appropriate.
- Focused run: `LINODE_CLI_TEST_MODE=1 XDG_CONFIG_HOME=$(mktemp -d) pytest tests/unit/test_request.py -k '<expr>'`.
