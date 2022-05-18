# Using the IPython and Jupyter Magic

Work with pandas and PRQL in an IPython terminal or Jupyter notebook.

## Implementation

This is a this wrapper around the fantastic
[IPython-sql][ipysql] magic.
Roughly speaking,
all we do is parse PRQL to SQL and pass that through to `ipython-sql`.
A full documentation of the supported features is available at their
[repository][ipysql].
Here,
we document those places where we differ from them,
plus those features we think you are mostly likely to find useful.

## Usage

### Installation

If you have already installed PyPRQL into your environment,
then you should be could to go!
We bundle in `IPython` and `pandas`,
though you'll need to install `Jupyter` separately.
If you haven't installed PyPRQL,
that's as simple as:

```shell
pip install PyPRQL
```

### Set Up

Open up either an `IPython` terminal or `Jupyter` notebook.
First,
we need to load the extension and connect to a database.

```python
In [1]: %load_ext pyprql.magic

In [2]: %prql duckdb:///:memory:

```

When connecting to a database,
pass the connection string as an argument to the line magic `%prql`.
The connection string needs to be in [SQLAlchemy format][conn_str],
so any connection supported by `SQLAlchemy` is supported by the magic.
Additional connection parameters can be passed as a dictionary using the `--connection_arguments`
flag to the the `%prql` line magic.
We ship with the necessary extensions to use [DuckDB][duckdb]
as the backend,
and here connect to an in-memory database.

However,
in-memory databases start off empty!
So,
we need to add some data.
This is where [pandas][pandas]
comes into play.
We can easily add a dataframe to the `DuckDB` database like so:

```python
In [3]: %prql --persist data

```

where data is a pandas dataframe we have already loaded.
This adds a table named `data` to the in-memory `DuckDB` instance.
If you connect to an existing SQL database,
then all the tables normally there will be accessible.

### Usage

:::{Important}
This is one area where we differe from `IPython-sql`.
We only support parasing PRQL as a cell magic,
not as a line magic.
:::

Now,
let's do a query!
By default,
`PRQLMagic` always returns the results as dataframe,
and always prints the results.
The results of the previous query are accessible in the `_` variable.

```python
In [4]: %%prql
from data
filter freq > 100
select [ food_name ]

Done.
Returning data to local variable _
       food_name
0        Abalone
1  Savoy cabbage
2           Kiwi
3       Angelica
```

If you want to,
you can capture the results into a different variable like so:

```python
In [5]: %%prql results <<
from data
filter freq > 100
select [ food_name ]

Done.
Returning data to local variable results
       food_name
0        Abalone
1  Savoy cabbage
2           Kiwi
3       Angelica
```

Now,
the output of the query is saved to `results`.

## Configuration

We strive to provide sane defaults;
however,
should you need to change settings,
a list of settings is available using the `%config` line magic.

```python
In [6]: %config PRQLMagic
PRQLMagic(SqlMagic) options
-------------------------
PRQLMagic.autocommit=<Bool>
    Set autocommit mode
    Current: True
PRQLMagic.autolimit=<Int>
    Automatically limit the size of the returned result sets
    Current: 0
PRQLMagic.autopandas=<Bool>
    Return Pandas DataFrames instead of regular result sets
    Current: True
PRQLMagic.autoview=<Bool>
    Display results
    Current: True
PRQLMagic.column_local_vars=<Bool>
    Return data into local variables from column names
    Current: False
PRQLMagic.displaycon=<Bool>
    Show connection string after execute
    Current: False
PRQLMagic.displaylimit=<Int>
    Automatically limit the number of rows displayed (full result set is still
    stored)
    Current: None
PRQLMagic.dsn_filename=<Unicode>
    Path to DSN file. When the first argument is of the form [section], a
    sqlalchemy connection string is formed from the matching section in the DSN
    file.
    Current: 'odbc.ini'
PRQLMagic.feedback=<Bool>
    Print number of rows affected by DML
    Current: True
PRQLMagic.short_errors=<Bool>
    Don't display the full traceback on SQL Programming Error
    Current: True
PRQLMagic.style=<Unicode>
    Set the table printing style to any of prettytable's defined styles
    (currently DEFAULT, MSWORD_FRIENDLY, PLAIN_COLUMNS, RANDOM)
    Current: 'DEFAULT'
```

If you want to change any of these,
you can do that with the `%config` line magic as well.

```python
In [7]: %config PRQLMagic.autoview = False
```

[ipysql]: https://github.com/catherinedevlin/ipython-sql
[conn_str]: https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls
[duckdb]: https://duckdb.org
[pandas]: https://pandas.pydata.org
