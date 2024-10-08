#
# Makefile for more convenient building of the Linode CLI and its baked content
#
MODULE :=
TEST_CASE_COMMAND :=
TEST_ARGS :=

ifdef TEST_CASE
TEST_CASE_COMMAND = -k $(TEST_CASE)
endif

# TODO: Remove this workaround once the LKE docs issue has been resolved
SPEC := https://gist.githubusercontent.com/lgarber-akamai/3e1d77f08acf1a7b29d63a77b0b4a289/raw/12f18d7b7b54cf8587c9f24e72509b0e530e5760/openapi.yaml

SPEC_VERSION ?= latest
ifndef SPEC
override SPEC = $(shell ./resolve_spec_url ${SPEC_VERSION})
endif

# Version-related variables
VERSION_FILE := ./linodecli/version.py
VERSION_MODULE_DOCSTRING ?= \"\"\"\nThe version of the Linode CLI.\n\"\"\"\n\n
LINODE_CLI_VERSION ?= "0.0.0.dev"

# Documentation-related variables
SPHINX_BUILDER ?= html
SPHINX_GENERATED_PATH := ./docs/_generated

.PHONY: install
install: check-prerequisites requirements build
	pip3 install --force dist/*.whl

.PHONY: bake
bake: clean
ifeq ($(SKIP_BAKE), 1)
	@echo Skipping bake stage
else
	python3 -m linodecli bake ${SPEC} --skip-config
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
	pip3 install --upgrade .[dev,obj]

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

.PHONY: testunit
testunit:
	@mkdir -p /tmp/linode/.config
	@orig_xdg_config_home=$${XDG_CONFIG_HOME:-}; \
	export LINODE_CLI_TEST_MODE=1 XDG_CONFIG_HOME=/tmp/linode/.config; \
	pytest -v tests/unit; \
	export XDG_CONFIG_HOME=$$orig_xdg_config_home

.PHONY: testint
testint:
	pytest tests/integration/${MODULE} ${TEST_CASE_COMMAND} ${TEST_ARGS}

.PHONY: testall
testall:
	pytest tests

# Alias for unit; integration tests should be explicit
.PHONY: test
test: testunit

.PHONY: clean-docs-commands
clean-docs-commands:
	rm -rf "$(SPHINX_GENERATED_PATH)"

.PHONY: generate-docs
generate-docs-commands: bake clean-docs-commands
	python3 -m linodecli generate-docs "$(SPHINX_GENERATED_PATH)"

.PHONY: generate-docs
generate-docs: generate-docs-commands
	cd docs && make $(SPHINX_BUILDER)

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

@PHONEY: smoketest
smoketest:
	pytest -m smoke tests/integration
