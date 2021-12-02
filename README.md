# znoyder

![](https://github.com/rhos-infra/znoyder/workflows/CI/badge.svg)

The goal of this project is to automate preparation of downstream CI jobs
for Red Hat OpenStack Platform (OSP) releases.

The name `znoyder` is a play of Silesian word *znojdywacz* and its English
meaning (*finder*).


# Usage examples - znoyder

After installing, the `znoyder` command is available to use.
For testing purposes, you may rely on `tox -e run --` command
or provided `run.sh` shell script as well.

Simply running `znoyder` with any valid subcommand will result in displaying
the default fields of corresponding data.

```
znoyder components
```

There is a basic filtering implemented that allows to limit and narrow results,
for example to a specific release, project or component – for `packages` subcommand.
It is also possible to select only certain fields as result, using the `--output` option.

```
znoyder packages --component network --tag osp-17.0 --output osp-patches
```

There exist the `--debug` option which will display raw dictionary as output.
It can be useful to find fields (key names) for `--output` option.

```
znoyder releases --debug
```

For further details, the standard `--help` shall guide you.

```
znoyder --help
```

# Usage examples - shperer
After installing, the `shperer` command is available to use.

Before running `shperer` CLI a set of projects should be available in the
local path.

To get list of jobs and templates defined for a particular project for a
particular zuul trigger simply type

```
shperer -d /path/to/neutron/ -b /path/to/templates/openstack-zuul-jobs -t check,gate
```

There exist the `-v` verbose option.

For further details, the standard `--help` shall guide you.

```
shperer --help
```

# Tests

Call `tox` to run the default test suite in this repository.
