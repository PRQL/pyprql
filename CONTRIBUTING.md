# Contributing

## Issues

If you think you've found a bug, or have an idea for a feature, let us know
[here][issues].

## Developing

If you think you can fix one of the bugs, or would like to submit a new feature,
then let's get coding!

Once you've cloned the repository, fork it, and get your development environment
set up. We use [poetry][poetry], [nox][nox], and [pre-commit][pre-commit] to
handle environments, testing, and linting. Between them, they make sure that all
checks run in isolated environments. If you don't have `poetry`, please see the
installation instructions [here][poetry_install]. Once you have poetry, you can
get set up with:

```{code-block} shell
poetry install
poetry run pre-commit install --install-hooks
```

Then, to run static checks, run:

```sh
pre-commit run -a
```

Pre-commit will automatically run [black][black], [mypy][mypy],
and ruff. When you push a change, GitHub
Actions will trigger a more robust suit using Nox, including security check and
automated documentation building.

### Commits

We use a GitHub Action for [python-semantic-release][psr] to manage our version
numbers. This automatically parses your commit messages to determine if a new
release is necessary, and, if so, what kind (ie. major, minor, patch). So your
commit message is important!

You can use a python implementation of [commitizen][cz] to handle that for you!
Just commit using `cz commit` instead of `git commit`.

### Documentation & testing

If you add new code, please add documentation and tests for it as well. We use
[napoleon numpy][docstrings] for our docstrings, and [sphinx][sphinx] for
automatic documentation. Our testing suite is [pytest][pytest].

## Releasing

pyprql uses [python-semantic-release][psr] to automate the release process.

To trigger a release, in the commit message add the terms `fix:`, `perf:`, or
`feat:`.

The version number will get updated automatically there is no need to update
them (in `pyproject.toml` and `pyprql/__init__.py`) manually.

[issues]: https://github.com/prql/pyprql/issues "Issues"
[poetry]: https://python-poetry.org/ "Poetry"
[poetry_install]: https://python-poetry.org/docs/#installation "Poetry Installation Instructions"
[nox]: https://nox.thea.codes/en/stable/ "Nox"
[pre-commit]: https://pre-commit.com/ "Pre-commit"
[black]: https://github.com/psf/black "Black"
[mypy]: https://mypy.readthedocs.io/en/stable/index.html "Mypy"
[psr]: https://github.com/relekang/python-semantic-release "Python Semantic Release"
[cz]: https://commitizen-tools.github.io/commitizen/index.html "Commitizen"
[docstrings]: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html "Numpy Napoleon Docstrings"
[sphinx]: https://www.sphinx-doc.org/en/master/index.html "Sphinx"
[pytest]: https://docs.pytest.org/en/7.0.x/ "pytest"
