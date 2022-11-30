#
# Makefile for more convenient building of the Linode CLI and its baked content
#

SPEC_VERSION ?= latest
ifndef SPEC
override SPEC = $(shell ./resolve_spec_url ${SPEC_VERSION})
endif

install: check-prerequisites requirements build
	ls dist/ | xargs -I{} pip3 install --force dist/{}

.PHONY: build
build: clean
	python3 -m linodecli bake ${SPEC} --skip-config
	cp data-3 linodecli/
	python3 setup.py bdist_wheel --universal

.PHONY: requirements
requirements:
	pip3 install -r requirements.txt

.PHONY: check-prerequisites
check-prerequisites:
	@ pip3 -v >/dev/null
	@ python3 -V >/dev/null

.PHONY: clean
clean:
	rm -f linodecli/data-*
	rm -f linode-cli.sh
	rm -f data-*
	rm -rf dist
