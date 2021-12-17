# Zuuler suite

![](https://github.com/rhos-infra/zuuler/workflows/CI/badge.svg)

The goal of this project is to automate preparation of downstream CI jobs
for Red Hat OpenStack Platform (OSP) releases.

The zuuler suite consists of the following tools:
– znoyder – finds the projects and their repositories,
– descarger – fetches from projects repositories the Zuul configuration,
– shperer – filters the Zuul configuration and converts to a sparser form,
– fertiger – adjusts and saves the new configuration for OSP specifics,
– ryhter – combines all the above together in a single workflow tool.

The name `znoyder` is a play of Silesian word *znojdywacz* and its English
meaning (*finder*).

The name `descarger` is a play of Spanish verb *descargar* and its English
meaning (*to download*).

The name `shperer` is a play of Polish term *szperacz* and its English
meaning (*rummager*).

The name `fertiger` is a play of Silesian adjective *fertig* and its English
meaning (*finished*).

The name `ryhter` is a play of Silesian verb *ryhtować* and its English
meaning (*to prepare*).


# Usage examples

The sections below provide brief description of each prepared tool.

For further details, the standard `--help` shall guide you.


## Znoyder

The tool can be used to browse **ospinfo** data.

Simply running `znoyder` with any valid subcommand will result
in displaying the default fields of corresponding data.
For example:

```
znoyder components
```

There is a basic filtering implemented that allows to limit and narrow results,
for example to a specific release, project or component – for `packages` subcommand.
It is also possible to select only certain fields as result, using the `--output` option.

```
znoyder packages --component network --tag osp-17.0 --output osp-patches
```

There exists the `--debug` option which will display raw dictionary as output.
It can be useful to find fields (key names) for `--output` option.

```
znoyder releases --debug
```


## Descarger

This tool downloads Zuul configuration, if there is any, from a given
repository and its branch.

```
descarger -r https://opendev.org/openstack/nova -b master -d zuul-config-files/
```


## Shperer

It allows investigating details of Zuul configuration.

Before running `shperer` CLI, a set of projects should be available in the
local path.

To get list of jobs and templates defined for a particular project
and a Zuul trigger types, simply execute:

```
shperer -d /path/to/neutron/ -b /path/to/templates/openstack-zuul-jobs -t check,gate
```

Note the tool requires absolute paths as an argument.

There exists the `-v` option for getting a verbose output with many details.


## Fertiger

It is mainly the templating tool for producing the adjusted configuration
files for OSP-specifics. Calling it will produce a list of jobs considered
during templates rendering and their remapping (if defined).

```
fertiger
```


## Ryhter

This tool can be used to download Zuul upstream configuration, then process it
and produce new configuration files, crafted for downstream OSP testing.

```
ryhter --generate
```

By default the tool only attempts to download all configuration files
for later processing, unless the `-g` option is given explicitly.


# Tests

Call `tox` to run the default test suite in this repository.
