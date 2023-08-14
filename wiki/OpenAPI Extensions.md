# Specification Extensions

In order to be more useful, the following [Specification Extensions](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#specificationExtensions) have been added to Linode's OpenAPI spec:

| Attribute | Location | Purpose |
| --- | --- | --- |
| x-linode-cli-action | method | The action name for operations under this path. If not present, operationId is used. |
| x-linode-cli-color | property | If present, defines key-value pairs of property value: color.  Colors must be one of "red", "green", "yellow", "white", and "black".  Must include a default. |
| x-linode-cli-command | path | The command name for operations under this path. If not present, "default" is used. |
| x-linode-cli-display | property | If truthy, displays this as a column in output.  If a number, determines the ordering (left to right). |
| x-linode-cli-format | property | Overrides the "format" given in this property for the CLI only.  Valid values are `file` and `json`. |
| x-linode-cli-skip | path | If present and truthy, this method will not be available in the CLI. |
| x-linode-cli-allowed-defaults| requestBody | Tells the CLI what configured defaults apply to this request. Valid defaults are "region", "image", "authorized_users", "engine", and "type". |
| x-linode-cli-nested-list | content-type| Tells the CLI to flatten a single object into multiple table rows based on the keys included in this value.  Values should be comma-delimited JSON paths, and must all be present on response objects. When used, a new key `_split` is added to each flattened object whose value is the last segment of the JSON path used to generate the flattened object from the source. |
| x-linode-cli-use-schema | content-type| Overrides the normal schema for the object and uses this instead. Especially useful when paired with ``x-linode-cli-nested-list``, allowing a schema to describe the flattened object instead of the original object. |
