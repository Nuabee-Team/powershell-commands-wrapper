# Contributing

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync
```

## Running tests

```bash
uv run pytest
```

Snapshot tests use [syrupy](https://github.com/syrupy-project/syrupy). If you
change the command-building logic, update the snapshots with:

```bash
uv run pytest --snapshot-update
```
then commit the changes (`.ambr` files).

## Linting and formatting

```bash
uv run ruff check .
uv run ruff format .
```

## Releasing

Releases are published to PyPI automatically when a `v*` tag is pushed:

```bash
git tag v1.2.3
```
Please respect semantic versioning.

The GitHub Actions release workflow builds the package, runs tests, and
publishes via trusted publishing — no manual token needed.
