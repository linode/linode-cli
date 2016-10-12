# python-linode-cli

A reimplementation of the Linode CLI using apinext and the Python Library.

### Goals

Right now, the goal of this project is to implement all of the features of
the [Linode CLI](https://www.linode.com/docs/platform/linode-cli) using the
[Python Library](https://github.com/linode/python-linode-api).  The purpose of this is twofold:

 1. To excersize the Python Library and get a feel for what could make it better.
 1. To have an easier way to interface with APIv4 from the command line.

There are some subtle difference in how the two work, mostly nuances in how Python's
argparser likes to handle things, but overall functionallity is very much the same.
This may change in the future as the new api introduces new concepts or phrasing that
would make sense to include here.

### Setup

Before setting up, be sure to have the dependencies:

  * python3
  * linode-api (latest) - `pip3 install --upgrade linode-api`
  * colorclass - `pip3 install colorclass`
  * terminaltables - `pip3 install terminaltables`

Right now, I recommend installing like so:

```bash
git clone <this_repo>
cd python-linode-cli
ln -s `pwd`/cli.py /usr/local/bin/linode-next
linode-next configure
````

I recommend using the name `linode-next` to avoid conflicts with the current Linode CLI,
which is installed to `/usr/local/bin/linode`.

### Configuration

As was mentioned in Setup, simply run `linode-next configure` to enter your Personal Access
Token and select defaults.  Configuration values are saved to `~/.linode-cli` as to not conflict
with the current Linode CLI's configuration in `~/.linodecli`

### How To Use

In general, you can use the [docs for the current Linode CLI](https://www.linode.com/docs/platform/linode-cli#using-the-cli)
as a reference.  At time of writing, only the `linode` series of commands is done.  Some examples follow:

###### Create a Linode

`linode-next create -l label -g group -P password`

###### Show Linodes

`linode-next list`

###### Boot a Linode

`linode-next start <linode-label>`

###### Shutdown a Linode

`linode-next stop <linode-label>`

###### Show Datacenters

`linode-next locations`
