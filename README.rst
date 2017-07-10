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
``linode-cli``.

When running the CLI for the first time, configure it by running
``linode-cli configure``.  This will prompt for for your API V4
personal access token and some defaults.

This is intended to be used like the existing Linode CLI, and you can
use `the existing CLI docs`_ for reference.

In addition, the following commands have been added:

- ``linode-cli event list`` - lists recent Events
- ``linode-cli event seen`` - marks all Events as seen
- ``linode-cli backups-show LINODE`` - show backups for a Linode
- ``linode-cli snapshot LINODE`` - create a snapshot of a Linode
- ``linode-cli backups-restore LINODE BACKUPID -l TARGET -f`` - restore a backup
- ``linode-cli backups-enable LINODE`` - enable backups for a Linode
- ``linode-cli backups-cancel LINODE`` - cancel backups for a Linode
- ``linode-cli ticket list`` - list tickets open on your account
- ``linode-cli ticket show TICKETID`` - show a ticket and its replies
- ``linode-cli volume list`` - list all Block Storage Volumes
- ``linode-cli volume show VOLUME`` - show information about a Volume

Examples
--------

List all linodes and their status:

``linode-cli list``

Create a new Linode with a root password of "hunter7" and label "cli-test-1"
in your default region with your default type:

``linode-cli create -P hunter7 -l cli-test-1``

Shut down your new linode:

``linode-cli stop cli-test-1``

Show a Linode's Backups:

``linode-cli backups-show cli-test-1``

List your domains:

``linode-cli domain list``

Show recent events:

``linode-cli event list``

Show open tickets:

``linode-cli ticket list``

.. _API v4: https://developers.linode.com
.. _Linode CLI: https://linode.com/cli
.. _Python Library: https://github.com/linode/python-linode-api
.. _the existing CLI docs: https://www.linode.com/docs/platform/linode-cli#using-the-cli
