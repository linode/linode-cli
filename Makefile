#
# Makefile for more convenient building of the Linode CLI and its baked content
#

PYTHON ?= 3

ifeq ($(PYTHON), 3)
	PYCMD=python3
else
	PYCMD=python
endif

install: common
	$(PYCMD) setup.py install

build: common
	$(PYCMD) setup.py bdist_wheel --universal

common:
	python linodecli bake ${SPEC} --skip-config
	python3 linodecli bake ${SPEC} --skip-config
	cp data-2 linodecli/
	cp data-3 linodecli/
