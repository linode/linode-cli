# plugin support

The Linode CLI supports embedded plugins, features that are hard-coded (instead
of generated as the rest of the CLI is) but are accessible directly through the
CLI as other features are.  All plugins are found in this directory.

## Creating a Plugin

To create a plugin, simply drop a new python file into this directory.  The
plugin must meet the following conditions:

 * Its name must be unique, both with the other plugins and with all commands
   offered through the generated CLI
 * Its name must not contain special characters, and should be easily enter able
   on the command line
 * It must support a `--help` command as all other CLI commands do.


## The Plugin Interface

All plugins are individual python files that reside in this directory.  Plugins
must have one function, `call`, that matches the following signature:

```
def call(args, context):
    """
    This is the function used to invoke the plugin.  It will receive the remaineder
    of sys.argv after the plugin's name, and a context of user defaults and config
    settings.
    """
```

### The PluginContext

The `PluginContext` class, passed as `context` to the `call` function, includes
all information the plugin is given during invocation.  This includes the following:

 * `token` - The Personal Access Token registered with the CLI to make requests
 * `client` - The CLI Client object that can make authenticated requests on behalf
    of the acting user.  This is preferrable to using `requests` or another library
    directly (see below).

#### CLI Client

The CLI Client provided as `context.client` can make authenticated API calls on
behalf of the user using the provided `call_operation` method.  This method is
invoked with a command and an action, and executes the given CLI command as if
it were entered into the command line, returning the resulting status code and
JSON data.

## Development

To develop a plugin, simply create a python source file in this directory that
has a `call` function as described above.  To test, simply build the CLI as
normal (via `make install`) or simply by running `./setup.py install` in the
root directory of the project (this installs the code without generating new
baked data, and will only work if you've installed the CLI via `make install`
at least once, however it's a lot faster).

### Examples

This directory contains two example plugins, `echo.py.example` and
`regionstats.py.example`.  To run these, simply remove the `.example` at the end
of the file and build the CLI as described above.
