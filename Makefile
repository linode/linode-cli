#
# Makefile for more convenient building of the Linode CLI and its baked content
#

SPEC_VERSION ?= latest
ifndef SPEC
override SPEC = $(shell ./resolve_spec_url ${SPEC_VERSION})
endif

# Version-related variables
VERSION_FILE := ./linodecli/version.py
VERSION_MODULE_DOCSTRING ?= \"\"\"\nThe version of the Linode CLI.\n\"\"\"\n\n
LINODE_CLI_VERSION ?= "0.0.0.dev"

BAKE_FLAGS := --debug

.PHONY: install
install: check-prerequisites requirements build
	pip3 install --force dist/*.whl

.PHONY: bake
bake: clean
ifeq ($(SKIP_BAKE), 1)
	@echo Skipping bake stage
else
	python3 -m linodecli bake ${SPEC} --skip-config $(BAKE_FLAGS)
	cp data-3 linodecli/
endif

.PHONY: create-version
create-version:
	@printf "${VERSION_MODULE_DOCSTRING}__version__ = \"${LINODE_CLI_VERSION}\"\n" > $(VERSION_FILE)

.PHONY: build
build: clean create-version bake
	python3 -m build --wheel --sdist

.PHONY: requirements
requirements:
	pip3 install --upgrade ".[dev,obj]"

.PHONY: lint
lint: build
	pylint linodecli
	isort --check-only linodecli tests
	autoflake --check linodecli tests
	black --check --verbose linodecli tests
	twine check dist/*

.PHONY: check-prerequisites
check-prerequisites:
	@ pip3 -v >/dev/null
	@ python3 -V >/dev/null

.PHONY: clean
clean:
	rm -f linodecli/data-*
	rm -f linode-cli.sh baked_version
	rm -f data-*
	rm -rf dist linode_cli.egg-info build

.PHONY: test-unit
test-unit:
	@mkdir -p /tmp/linode/.config
	@orig_xdg_config_home=$${XDG_CONFIG_HOME:-}; \
	export LINODE_CLI_TEST_MODE=1 XDG_CONFIG_HOME=/tmp/linode/.config; \
	pytest -vv tests/unit; \
	exit_code=$$?; \
	export XDG_CONFIG_HOME=$$orig_xdg_config_home; \
	exit $$exit_code

# Integration Test Arguments
# TEST_SUITE: Optional, specify a test suite (e.g. domains), Default to run everything if not set
# TEST_CASE: Optional, specify a test case (e.g. 'test_create_a_domain')
# TEST_ARGS: Optional, additional arguments for pytest (e.g. '-v' for verbose mode)

.PHONY: test-int
test-int:
	pytest tests/integration/$(TEST_SUITE) $(if $(TEST_CASE),-k $(TEST_CASE)) $(TEST_ARGS)

.PHONY: testall
testall:
	pytest tests

# Alias for unit; integration tests should be explicit
.PHONY: test
test: test-unit

.PHONY: black
black:
	black linodecli tests

.PHONY: isort
isort:
	isort linodecli tests

.PHONY: autoflake
autoflake:
	autoflake linodecli tests

.PHONY: format
format: black isort autoflake

@PHONEY: test-smoke
test-smoke:
	pytest -m smoke tests/integration
