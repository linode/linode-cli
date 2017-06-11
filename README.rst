linode-cli
==========

A reimplementation of the `Linode CLI`_ using the `Python Library`_ and
`API V4`_.

Installation
------------
::

    pip3 install linode-cli

Building from Source
-------------------

To build this package from source:

- Clone this repository.
- ``python3 setup.py install``

Usage
-----

While the Linode API V4 is in beta, this package installs the command
``linode-beta``.

When running the CLI for the first time, configure it by running
``linode-beta configure``.  This will prompt for for your API V4
personal access token and some defaults.

This is intended to be used like the existing Linode CLI, and you can
use `the existing CLI docs`_ for reference.

In addition, the following commands have been added:

- ``linode-beta event list`` - lists recent Events
- ``linode-beta event seen`` - marks all Events as seen
- ``linode-beta backups-show LINODE`` - show backups for a Linode
- ``linode-beta snapshot LINODE`` - create a snapshot of a Linode
- ``linode-beta backups-restore LINODE BACKUPID -l TARGET -f`` - restore a backup

Examples
--------

List all linodes and their status:

``linode-beta list``

Create a new Linode with a root password of "hunter7" and label "cli-test-1"
in your default region with your default type:

``linode-beta create -P hunter7 -l cli-test-1``

Shut down your new linode:

``linode-beta stop cli-test-1``

Show a Linode's Backups:

``linode-beta backups-show cli-test-1``

List your domains:

``linode-beta domain list``

Show recent events:

``linode-beta event list``

.. _API v4: https://developers.linode.com
.. _Linode CLI: https://linode.com/cli
.. _Python Library: https://github.com/linode/python-linode-api
.. _the existing CLI docs: https://www.linode.com/docs/platform/linode-cli#using-the-cli
