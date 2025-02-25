# Customizing Output

## Changing Output Fields

By default, the CLI displays on some pre-selected fields for a given type of
response.  If you want to see everything, just ask::
```bash
linode-cli linodes list --all-columns
```

Using `--all-columns` will cause the CLI to display all returned columns of
output.  Note that this will probably be hard to read on normal-sized screens
for most actions.

If you want even finer control over your output, you can request specific columns
be displayed::
```bash
linode-cli linodes list --format 'id,region,status,disk,memory,vcpus,transfer'
```

This will show some identifying information about your Linode as well as the
resources it has access to.  Some of these fields would be hidden by default -
that's ok.  If you ask for a field, it'll be displayed.

## Output Formatting

While the CLI by default outputs human-readable tables of data, you can use the
CLI to generate output that is easier to process.

## Machine Readable Output

To get more machine-readable output, simply request it::
```bash
linode-cli linodes list --text
```

If a tab is a bad delimiter, you can configure that as well::
```bash
linode-cli linodes list --text --delimiter ';'
```

You may also disable header rows (in any output format)::
```bash
linode-cli linodes list --no-headers --text
```

## JSON Output

To get JSON output from the CLI, simple request it::
```bash
linode-cli linodes list --json --all-columns
```

While the `--all-columns` is optional, you probably want to see all output
fields in your JSON output.  If you want your JSON pretty-printed, we can do
that too::
```bash
linode-cli linodes list --json --pretty --all-columns
```
