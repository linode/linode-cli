# Example Third Party Plugin

This is included as an example of how to develop a third party plugin for the
Linode CLI.  There are only two files:

#### example_third_party_plugin.py

This file contains the python source code for your plugin.  Notably, it is a valid
plugin because it exposes two attributes at the module level:

 * `PLUGIN_NAME` - a constant whose value is the string used to invoke the plugin
   once it's registered
 * `call(args, context)` - a function called when the plugin is invoked

While this example is a single file, a module that exposes those two attributes
at the top level is also a valid CLI plugin (define or import them in the module's
`__init__.py` file to expose them at the module level).


#### setup.py

This file is used by setuptools to create a python module.  This example is very
sparse, but is enough to install the module locally and get you started.  Please
see the [setuptools docs](https://setuptools.readthedocs.io/en/latest/index.html)
for all available options.

## Installation

To install this example plugin, run the following in this directory:

```bash
python setup.py install
```

### Registration and Invocation

Once installed, you have to register the plugin with the Linode CLI by python
module name (as defined in `setup.py`):

```bash
linode-cli register-plugin example_third_party_plugin
```

The CLI will print out the command to invoke this plugin, which in this example
is:


```bash
linode-cli example-plugin
```

Doing so will print `Hello world!` and exit.

## Development

To begin working from this base, simply edit `example_third_party_plugin.py` and
add whatever features you need.  When it comes time to distribute your plugin,
copy this entire directory elsewhere and modify the `setup.py` file as described
within it to create your own module.

To test your changes, simply reinstall the plugin as described above.  This
_does not_ require reregistering it, as it references the installed module and
will invoke the updated code next time it's called.
