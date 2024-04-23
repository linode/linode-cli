# Installation

## PyPi

```bash
pip3 install linode-cli
# for upgrading
pip3 install linode-cli --upgrade
```

## Docker

### Token
```bash
docker run --rm -it -e LINODE_CLI_TOKEN=$LINODE_TOKEN linode/cli:latest linodes list
```

### Config
```bash
docker run --rm -it -v $HOME/.config/linode-cli:/home/cli/.config/linode-cli linode/cli:latest linodes list
```

## GitHub Actions

[Setup Linode CLI](https://github.com/marketplace/actions/setup-linode-cli) GitHub Action to automatically install and authenticate the cli in a GitHub Actions environment:
```yml
- name: Install the Linode CLI
  uses: linode/action-linode-cli@v1
  with:
    token: ${{ secrets.LINODE_TOKEN }}
```

## Community Distributions

The Linode CLI is available through unofficial channels thanks to our awesome community! These distributions are not included in release testing.

### Homebrew

```bash
brew install linode-cli
brew upgrade linode-cli
```
# Building from Source

In order to successfully build the CLI, your system will require the following:

- The `make` command
- `python3`
- `pip3` (to install project dependencies)

Before attempting a build, install python dependencies like this::
```bash
make requirements
```

Once everything is set up, you can initiate a build like so::
```bash
make build
```

If desired, you may pass in `SPEC=/path/to/openapi-spec` when running `build`
or `install`.  This can be a URL or a path to a local spec, and that spec will
be used when generating the CLI.  A yaml or json file is accepted.

To install the package as part of the build process, use this command::

```bash
make install
```
