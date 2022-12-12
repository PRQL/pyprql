# pyprql

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![PyPI - License](https://img.shields.io/pypi/l/pyprql)
![PyPI](https://img.shields.io/pypi/v/pyprql)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyprql)

[![Documentation Status](https://readthedocs.org/projects/pyprql/badge/?version=latest)](https://pyprql.readthedocs.io/en/latest/?badge=latest)
![Discord](https://img.shields.io/discord/936728116712316989)
![GitHub contributors](https://img.shields.io/github/contributors/prql/pyprql)
![GitHub Repo stars](https://img.shields.io/github/stars/prql/pyprql)

[![CI/CD](https://github.com/prql/pyprql/actions/workflows/pull-request.yaml/badge.svg?branch=main)](https://github.com/prql/pyprql/actions/workflows/pull-request.yaml)
[![codecov](https://codecov.io/gh/prql/pyprql/branch/main/graph/badge.svg?token=C6J2UI7FR5)](https://codecov.io/gh/prql/pyprql)

[![Codestyle: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

pyprql contains

- pyprql.pandas_accessor — Pandas integration for PRQL
- pyprql.magic — IPython magic for connecting to databases using `%%prql`

For docs, Check out the [pyprql Docs](https://pyprql.readthedocs.io/), and the
[PRQL Book][prql_docs].

This project was created by
[@charlie-sanders](https://github.com/charlie-sanders/) &
[@rbpatt2019](https://github.com/rbpatt2019) and is now maintained by the
broader PRQL team.

## Installation

```bash
pip install pyprql
```

## Examples

### Pandas integration

```python
import pandas as pd
import pyprql.pandas_accessor

df = (...)
results_df = df.prql.query('select [age,name,occupation] | filter age > 21')
```

### Jupyter Magic

```python
In [1]: %load_ext pyprql.magic
In [2]: %prql postgresql://user:password@localhost:5432/database
In [3]: %%prql
   ...: from p
   ...: group categoryID (
   ...:   aggregate [average unitPrice]
   ...: )
In [4]: %%prql results <<
   ...: from p
   ...: aggregate [min unitsInStock, max unitsInStock]

```

[prql_docs]: https://prql-lang.org/reference
