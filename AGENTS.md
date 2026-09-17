# Repository Guide

## Setup
- Use `make requirements` for local setup. It installs `.[dev,obj]`; plain `.[dev]` misses `boto3`, which the object-storage plugin and tests use.
- Use a virtualenv if possible; package metadata requires Python `>=3.9`, CI tests Python 3.9 through 3.13, and the Dockerfile builds on Python 3.13.
- On a clean machine, export `LINODE_CLI_TOKEN` before running CLI commands that should not enter interactive `configure()`. Unit tests avoid config prompts with `LINODE_CLI_TEST_MODE=1`.
- `make install` is the closest local equivalent to CI setup, but it is heavyweight: `check-prerequisites -> requirements -> build -> pip3 install --force dist/*.whl`.
- The wiki setup page is mostly useful, but the wiki testing page has stale target names. Trust the `Makefile`: use `make test-unit` and `make test-int`, not `make testunit` or `make testint`.

## Generated Files
- This CLI is spec-driven. Runtime commands load the baked pickle at `linodecli/data-3`; `MANIFEST.in` packages that file into distributions.
- `make build`, `make install`, and `make lint` all run generation through `build`: `clean`, rewrite `linodecli/version.py` from `LINODE_CLI_VERSION` (default `0.0.0.dev`), regenerate root `data-3`, copy it to `linodecli/data-3`, and rebuild `dist/`.
- Prefer `make bake SPEC=/path/to/openapi.json` or `make bake SPEC_VERSION=<tag>`; it resolves the spec via `./resolve_spec_url` when needed, passes `$(BAKE_FLAGS)` (`--debug` by default), and copies root `data-3` to `linodecli/data-3`.
- If you rely on the default `SPEC_VERSION=latest`, set `GITHUB_TOKEN`; `resolve_spec_url` calls the GitHub releases API for `linode/linode-api-openapi` and can hit rate limits without it.
- Manual bake: `python3 -m linodecli bake <spec> --skip-config` writes root `data-3` only; copy it to `linodecli/data-3` yourself or the package keeps the old pickle. `--skip-config` is a hidden sentinel checked in `linodecli/__init__.py` before argparse/config bootstrapping.
- Never hand-edit `linodecli/data-3` or root `data-3`; change bake logic or the source spec/extensions and rebake.
- `CLI._load_openapi_spec()` mutates parsed specs with `_normalize_content_parameters()` before `openapi3.OpenAPI(...)`; this converts OpenAPI Parameter `content` forms to top-level `schema` because the `openapi3` package does not support parameter `content` directly.

## Code Map
- Importing top-level `linodecli` has side effects: `linodecli/__init__.py` constructs a global `CLI`, loads baked ops, and may load/configure user state immediately.
- CLI entrypoints are `linodecli/__init__.py:main` and `linodecli/__main__.py`; console scripts `linode-cli`, `linode`, and `lin` all point to `linodecli:main`.
- `linodecli/cli.py` handles spec loading/baking, baked-op loading, command lookup, custom aliases, and dispatch.
- `linodecli/api_request.py` builds request URLs, request bodies, `X-Filter`, retries, version warnings, and error output.
- `linodecli/output/output_handler.py` handles table, ASCII table, delimited, JSON, and Markdown output. `linodecli/overrides.py` contains command/action/output-mode-specific display overrides.
- `linodecli/configuration/` owns config loading, interactive configuration, OAuth token flow, env token handling, and API URL overrides.
- `linodecli/plugins/` contains hand-written commands outside the generated OpenAPI surface. If you add or change a plugin, read `linodecli/plugins/README.md` for the `call(args, context)` interface and third-party `PLUGIN_NAME` requirement.
- If you touch `linodecli/baked/*.py`, read `linodecli/baked/AGENTS.md` first. Key constraint: baked model state must stay pickle-safe.

## Tests
- `make test` only runs unit tests; it is an alias for `make test-unit`.
- Use `make test-unit` for normal unit verification. It sets `LINODE_CLI_TEST_MODE=1` and `XDG_CONFIG_HOME=/tmp/linode/.config` so imports do not trigger interactive config.
- Focused unit test: `LINODE_CLI_TEST_MODE=1 XDG_CONFIG_HOME=$(mktemp -d) pytest tests/unit/test_cli.py -k '<expr>'`.
- Unit tests for bake/parsing behavior use minimal OpenAPI fixtures in `tests/fixtures/` and helper fixtures in `tests/unit/conftest.py`; add or update a fixture there when changing generated argument/response behavior.
- Integration tests shell out to the installed `linode-cli` binary, not the source tree directly. Re-run `make install` after code changes before trusting integration results.
- Integration and smoke tests hit the real Linode API and create/destroy real resources. Do not run them casually against a personal account.
- `tests/integration/conftest.py` has a session-scoped autouse firewall fixture, so even focused integration runs can create a cloud firewall before the selected test body runs.
- Focused integration run: `make test-int TEST_SUITE=domains TEST_CASE=test_create_a_domain TEST_ARGS='-v'`.
- Integration and smoke tests require `LINODE_CLI_TOKEN`. Long-running cases are skipped unless `RUN_LONG_TESTS=True` exactly. Smoke tests are `make test-smoke`.

## Lint And Format
- `make lint` is not a pure lint pass; it depends on `make build`, so it cleans, rebakes, rebuilds `dist/`, then runs `pylint`, `isort --check-only`, `autoflake --check`, `black --check`, and `twine check dist/*`.
- Because lint rebakes, default `SPEC_VERSION=latest` needs GitHub API access (and often `GITHUB_TOKEN`). Without `SPEC=...` or a token, `make lint` can fail on rate limits during bake, not only on style.
- For quick checks without generation side effects, run style tools directly, for example `black --check linodecli tests`, `isort --check-only linodecli tests`, or `autoflake --check linodecli tests`.
- Formatting uses Black/isort with an 80-character line length. `make format` runs `black`, then `isort`, then `autoflake` and rewrites files in place.
- Keep syntax compatible with Python 3.9 even if developing on a newer interpreter.

## Workflow
- CI enforces PR titles matching `TPT-<number>: <description>` unless the PR is labeled `dependencies`, `hotfix`, `community-contribution`, or `ignore-for-release`.
- `e2e_scripts/` is a git submodule used by CI/e2e workflows, not the core CLI package. Fresh clones leave it empty until `git submodule update --init`.
- If you change behavior, commands, generated-file flow, test/lint setup, or architecture described here, update this `AGENTS.md` in the same change.
