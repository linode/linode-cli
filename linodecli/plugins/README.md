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
