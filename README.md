# pyprql

[![CI/CD](https://github.com/prql/pyprql/actions/workflows/pull-request.yaml/badge.svg?branch=main)](https://github.com/prql/pyprql/actions/workflows/pull-request.yaml)
[![Documentation Status](https://readthedocs.org/projects/pyprql/badge/?version=latest)](https://pyprql.readthedocs.io/en/latest/?badge=latest)

![PyPI](https://img.shields.io/pypi/v/pyprql)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyprql)
[![Codestyle: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<!-- [![codecov](https://codecov.io/gh/prql/PyPrql/branch/main/graph/badge.svg?token=C6J2UI7FR5)](https://codecov.io/gh/prql/PyPrql) -->

pyprql contains:

- pyprql.pandas_accessor — Pandas integration for PRQL
- pyprql.magic — IPython magic for connecting to databases using `%%prql`
- pyprql.compile — An export of `prql-python`'s `compile` function

For docs, check out the [pyprql docs](https://pyprql.readthedocs.io/), and the
[PRQL Book][prql_docs].

## Installation

```sh
pip install pyprql
```

## Usage

### Pandas integration

```python
import pandas as pd
import pyprql.pandas_accessor

df = (...)
results_df = df.prql.query("select [age,name,occupation] | filter age > 21")
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

### Compilation

This library exposes `prql-python.compile`, so we can simply generate SQL:

```python
import pyprql
pyprql.compile("from artists | select track")
print(pyprql.compile("from artists | select track"))
```

...returns...

```sql
SELECT
  track
FROM
  artists
```

For context, `prql-python` is the Python binding for `prql-compiler`, so only
contains functions for compilation; and this library offers broader python
integrations and tooling.

## Support

This project was created by
[@charlie-sanders](https://github.com/charlie-sanders/) &
[@rbpatt2019](https://github.com/rbpatt2019) and is now maintained by the
broader PRQL team.

[prql_docs]: https://prql-lang.org/book
