# PyPrql

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![PyPI - License](https://img.shields.io/pypi/l/pyprql)
![PyPI](https://img.shields.io/pypi/v/pyprql)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyprql)

[![Documentation Status](https://readthedocs.org/projects/pyprql/badge/?version=latest)](https://pyprql.readthedocs.io/en/latest/?badge=latest)
![Discord](https://img.shields.io/discord/936728116712316989)
![GitHub contributors](https://img.shields.io/github/contributors/prql/pyprql)
![GitHub Repo stars](https://img.shields.io/github/stars/prql/pyprql)

[![CI/CD](https://github.com/prql/PyPrql/actions/workflows/cicd.yaml/badge.svg?branch=main)](https://github.com/prql/PyPrql/actions/workflows/cicd.yaml)
[![codecov](https://codecov.io/gh/prql/PyPrql/branch/main/graph/badge.svg?token=C6J2UI7FR5)](https://codecov.io/gh/prql/PyPrql)

[![Codestyle: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

Python TUI for CSV files and database connections.  See [prql-python](https://pypi.org/project/prql-python/) for just bindings.  

For docs, Check out the [PyPRQL Docs](https://pyprql.readthedocs.io/), and the [PRQL Book][prql_docs].

This project is maintained by [@charlie-sanders](https://github.com/charlie-sanders/) and [@rbpatt2019](https://github.com/rbpatt2019)

## Installation

```bash
pip install pyprql
```

### Try it out

#### CSV file

```bash
curl https://people.sc.fsu.edu/~jburkardt/data/csv/zillow.csv
pyprql zillow.csv
```

#### Database

```bash
pyprql "sqlite:///your_database.db"
PRQL> show tables
```

### The pyprql tool

* pyprql can connect to any database that SQLAlchemy supports, execute `pyprql` without arguments for docs on how to install drivers.
* pyprql can connect to CSV files,  replace the connection string with the file path and it will load the CSV into a temporary SQLite database.
* pyprql can save the results with a `| to csv ${filename}` transform at the end of the query
* pyprql has auto-completion on table names and table aliases with _tab_, and history-completion with _alt-f_

[prql]: https://github.com/prql/prql
[prql_docs]: https://prql-lang.org/reference
