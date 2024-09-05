Installation
============

This document outlines the officially supported installation methods for the Linode CLI.

PyPi
----

The Linode CLI is automatically released to PyPI and can be installed using `pip`::

    python3 -m pip install linode-cli

The following can be used to upgrade an existing installation of the Linode CLI::

    pip3 install linode-cli --upgrade

Docker
------

The Linode CLI is also officially distributed as a `Docker Image <https://hub.docker.com/r/linode/cli>`_.

Authenticating with a Personal Access Token
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following command runs the `linodes list` command in a Docker container
using an existing `Personal Access Token <https://techdocs.akamai.com/cloud-computing/docs/manage-personal-access-tokens>`_::

    docker run --rm -it -e LINODE_CLI_TOKEN=$LINODE_TOKEN linode/cli:latest linodes list

Authenticating with an Existing Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following command runs the `linodes list` command in a Docker container
using an existing Linode CLI configuration file::

    docker run --rm -it -v $HOME/.config/linode-cli:/home/cli/.config/linode-cli linode/cli:latest linodes list

GitHub Actions
--------------

The Linode CLI can automatically be installed in a GitHub Actions runner environment using the
`Setup Linode CLI Action <https://github.com/marketplace/actions/setup-linode-cli>`_:

.. code-block:: yaml

    - name: Install the Linode CLI
      uses: linode/action-linode-cli@v1
      with:
        token: ${{ secrets.LINODE_TOKEN }}


Community Distributions
-----------------------

The Linode CLI is available through unofficial channels thanks to our awesome community!
These distributions are not included in release testing.

Homebrew
^^^^^^^^

.. code-block::

    brew install linode-cli
    brew upgrade linode-cli

Building from Source
--------------------

In order to successfully build the CLI, your system will require the following:

- The `make` command
- `python3`
- `pip3` (to install project dependencies)

Before attempting a build, ensure all necessary dependencies have been installed::

    make requirements

Once everything is set up, you can initiate a build like so::

    make build

If desired, you may pass in ``SPEC=/path/to/openapi-spec`` when running ``build``
or ``install``.  This can be a URL or a path to a local spec, and that spec will
be used when generating the CLI.  A yaml or json file is accepted.

To install the package as part of the build process, use this command::

    make install

.. rubric:: Next Steps

To continue to the next step of this guide, continue to the :ref:`Configuration page <general_configuration>`.
