#
# Makefile for more convenient building of the Linode CLI and its baked content
#
INTEGRATION_TEST_PATH :=
TEST_CASE_COMMAND :=

ifdef TEST_CASE
TEST_CASE_COMMAND = -k $(TEST_CASE)
endif


SPEC_VERSION ?= latest
ifndef SPEC
override SPEC = $(shell ./resolve_spec_url ${SPEC_VERSION})
endif

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

.PHONY: build
build: clean bake
	python3 -m build --wheel --sdist

.PHONY: requirements
requirements:
	pip3 install -r requirements.txt -r requirements-dev.txt

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
testunit: export LINODE_CLI_TEST_MODE = 1
testunit:
	pytest -v tests/unit

.PHONY: testint
testint:
	pytest tests/integration/${INTEGRATION_TEST_PATH} ${TEST_CASE_COMMAND} --disable-warnings

.PHONY: testall
testall:
	pytest tests

# Alias for unit; integration tests should be explicit
.PHONY: test
test: testunit

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
	pytest -m smoke tests/integration --disable-warnings
