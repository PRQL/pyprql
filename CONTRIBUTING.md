# Contributing

````{admonition} TLDR
:class: tip

Create a virtual environment with your preferred tool.
Then run `pre-commit install --install-hooks`.
Then commit with `cz commit`,
and everything should take care of itself!
````

Welcome, friend!
Open-source software isn't open open-source without the community.
We appreciate your interest and welcome all contributions.
While your here,
we respectfully ask that you abide by our [code of conduct](./coc.md).
To help keep everything moving smoothly,
we have a few guidelines.

## Bugs

If you think you've found a bug,
let us know [here][issues].
We'll do our best to deal with it ASAP,
but please be patient as we also work many other projects!

## Developing

If you think you can fix one of the bugs,
or would like to submit a new feature,
then let's get coding!

Once you've cloned the repository,
fork it,
and get your development environment set up.
We use [poetry][poetry],
[nox][nox],
and [pre-commit][pre-commit]
to handle environments, testing, and linting.
Between them,
they make sure that all checks run in isolated environments.
If you don't have `poetry`,
please see the installation instructions [here][poetry_install].
Once you have poetry,
you can get set up with:

```{code-block} shell
poetry install
poetry run pre-commit install --install-hooks
```

Now,
you don't even have to think about linting or testing.
When you commit a change,
pre-commit will automatically run [black][black],
[isort][isort],
[mypy][mypy],
and a suite of [flake8][flake8]-based linters.
When you push a change,
github actions will trigger a more robust suit using Nox,
including security check and automated documentation building.

### Commits

We use a GitHub action for
[python-semantic-release][psr]
to manage our version numbers.
This automatically parses your commit messages to determine if a new release is nesessary,
and, if so, what kind (ie. major, minor, patch).
So your commit message is very important!

But we also don't want you stressing about how to format your commit message.
To that end,
we use a python implementation of
[commitizen][cz]
to handle that for you!
Just commit using `cz commit` instead of `git commit`,
and enjoy the magic!

### Documentation and Testing

Speaking of documentation and testing -
if you add new code,
please add documentation and tests for it as well.
We use [napoleon numpy][docstrings]
for our docstrings,
and [sphinx][sphinx] for automatic documentation.
Our testing suite is [pytest][pytest].

## Review

Once your happy with your code,
open a pull-request,
and we will reveiw ASAP.
If you pull-request is not passing on github actions,
or something else confuses us
(we are, after all, only human!),
we might ask for some small changes.
Once everything is looking good,
we will merges in your changes!

## From the Command-Line

```{admonition} :fireworks: Optional fun!

None of this section is required, but we find it useful and hope you do, too!
```

If you haven't heard of it already,
give a peek to to [gh][gh],
GitHub's official CLI.
It allows to manage all of the above steps from the command-line,
from forking,
to raising issues,
and checking on the status of your pull request.
Not a necessity,
but for you terminal warriors out there,
it just might help!

[issues]: https://github.com/prql/pyprql/issues "Issues"
[gh]: https://github.com/cli/cli "GH CLI"
[poetry]: https://python-poetry.org/ "Poetry"
[poetry_install]: https://python-poetry.org/docs/#installation "Poetry Installation Instructions"
[nox]: https://nox.thea.codes/en/stable/ "Nox"
[pre-commit]: https://pre-commit.com/ "Pre-commit"
[black]: https://github.com/psf/black "Black"
[isort]: https://pycqa.github.io/isort/ "iSort"
[mypy]: https://mypy.readthedocs.io/en/stable/index.html "Mypy"
[flake8]: https://flake8.pycqa.org/en/latest/ "Flake8"
[psr]: https://github.com/relekang/python-semantic-release "Python Semantic Release"
[cz]: https://commitizen-tools.github.io/commitizen/index.html "Commitizen"
[docstrings]: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html "Numpy Napoleon Docstrings"
[sphinx]: https://www.sphinx-doc.org/en/master/index.html "Sphinx"
[pytest]: https://docs.pytest.org/en/7.0.x/ "pytest"
