# Znoyder

![](https://github.com/rhos-infra/znoyder/workflows/CI/badge.svg)

The goal of this project is to automate preparation of downstream CI jobs
for Red Hat OpenStack Platform (OSP) releases.

The name `znoyder` is a play of Silesian word *znojdywacz* and its English
meaning (*finder*).


# Usage examples

Below are the examples of the tool usage.
The basic usage involves a valid subcommand and additional options to it.
For further details, the standard `--help` shall guide you.


## browse-osp

This command can be used to explore the **ospinfo** data.

To view existing components:
```
znoyder browse-osp components
```

There is a basic filtering implemented that allows to limit and narrow results,
for example to a specific release, project or component – for `packages` subcommand.
It is also possible to select only certain fields as result, using the `--output` option.

To list URLs to repositories of packages that belong to network component:

```
znoyder browse-osp packages --component network --tag osp-17.0 --output osp-patches
```

There exists the `--debug` option which will display raw dictionary as output.
It can be useful to find fields (key names) for `--output` option.

```
znoyder browse-osp releases --debug
```


## download

This command allows fetching the Zuul configuration, if there is any,
from a given repository and its branch.

```
znoyder download --repo https://opendev.org/openstack/nova --branch master --destination zuul-config-files/
```


## find-jobs

It allows investigating details of Zuul configuration that is available
in the local path.

To get list of jobs and templates defined for a particular project
and a specified Zuul trigger types, simply execute:

```
znoyder find-jobs --dir path/to/nova --base /path/to/templates/openstack-zuul-jobs --trigger check,gate
```

There exists the `-v` option for getting a verbose output with many details.


## templates

Calling this command will produce a list of jobs considered during
templates rendering and their remapping (if defined).

```
znoyder templates --json
```


## generate

This command can be used to download Zuul upstream configuration for a given
OSP release and component (optional filtering), then process it and produce
new configuration files, crafted for downstream OSP testing.

```
znoyder generate --tag osp-17.0 --component network --collect-all
```


# Tests

Call `tox` to run the default test suite in this repository.
