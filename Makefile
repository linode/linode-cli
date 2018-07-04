#
# Makefile for more convenient building of the Linode CLI and its baked content
#

PYTHON ?= 3
SPEC ?= https://developers.linode.com/openapi.yaml

ifeq ($(PYTHON), 3)
	PYCMD=python3
else
	PYCMD=python
endif

install: check-prerequisites requirements build
	$(PYCMD) setup.py install

.PHONY: build
build: common
	$(PYCMD) setup.py bdist_wheel --universal

.PHONY: common
common:
	python -m linodecli bake ${SPEC} --skip-config
	python3 -m linodecli bake ${SPEC} --skip-config
	cp data-2 linodecli/
	cp data-3 linodecli/

.PHONY: requirements
requirements:
	pip install -r requirements.txt
	pip3 install -r requirements.txt

.PHONY: check-prerequisites
check-prerequisites:
	@ pip -v >/dev/null
	@ pip3 -v >/dev/null
	@ python -V >/dev/null
	@ python3 -V >/dev/null
