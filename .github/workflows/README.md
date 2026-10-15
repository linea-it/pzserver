# Workflows

The .yml files in this directory are used to define the various continuous
integration scripts that will be run on your behalf e.g. nightly as a smoke check,
or when you create a new PR.

For more information about CI and workflows, look here: https://lincc-ppt.readthedocs.io/en/latest/practices/ci.html

Or if you still have questions contact us: https://lincc-ppt.readthedocs.io/en/latest/source/contact.html

## Dependency compatibility checks

The lowest-version and Rubin compatibility workflows run on pull requests,
pushes to `main`, and manual dispatches. They do not contain scheduled triggers,
so GitHub cannot disable required pull-request checks when scheduled workflows
are disabled because of repository inactivity.

`daily-dependency-compatibility.yml` owns the daily schedule and calls these
workflows through `workflow_call`:

- `lowest-versions.yml`
- `rubin-recommended-compatibility.yml`
- `rubin-latest-daily-compatibility.yml`

The following checks should be required by the `main` branch protection rule:

- `pre-commit-ci`
- `lowest_direct_dependencies`
- `rubin_recommended_compatibility`
- `rubin_latest_daily_compatibility`
- `test_and_coverage (3.11)`
- `test_and_coverage (3.12)`
- `test_and_coverage (3.13)`
