# Using the IPython and Jupyter Magic

Work with pandas and PRQL in an IPython terminal or Jupyter notebook.

## Implementation

This is a thin wrapper around [ploomber/jupysql][jupysql] magic. Full
documentation of the supported features is available at their
[repository][jupysql]. Here, we document the most salient features or those
where we differ.

## Usage

### Installation

If you have already installed pyprql into your environment,
then you should be could to go!
We bundle in `IPython` and `pandas`,
though you'll need to install `Jupyter` separately.
If you haven't installed pyprql,
that's as simple as:

```shell
pip install pyprql
```

### Set Up

Open up either an `IPython` terminal or `Jupyter` notebook. First, we need to
load the extension and connect to a database.

```
In [1]: %load_ext pyprql.magic

```

#### Connecting a database

We have two options for connecting a database

1. Create an in-memory DB. This is the easiest way to get started.

   ```
   In [2]: %prql duckdb:///:memory:
   ```

   However, in-memory databases start off empty! So, we need to add some data.
   We have a two options:

   - We can easily add a [pandas][pandas] dataframe to the `DuckDB` database
     like so:

     ```
     In [3]: %prql --persist df
     ```

     where `df` is a pandas dataframe. This adds a table named `df` to the
     in-memory `DuckDB` instance.

   - Or download a CSV and query it directly, with DuckDB:

     ```
     !wget https://raw.githubusercontent.com/graphql-compose/graphql-compose-examples/master/examples/northwind/data/csv/products.csv
     ```

     ...and then `from products.csv` will work.

2. Connect to an existing database

   When connecting to a database, pass the connection string as an argument to the
   line magic `%prql`. The connection string needs to be in [SQLAlchemy
   format][conn_str], so any connection supported by `SQLAlchemy` is supported by
   the magic. Additional connection parameters can be passed as a dictionary using
   the `--connection_arguments` flag to the the `%prql` line magic. We ship with
   the necessary extensions to use [DuckDB][duckdb] as the backend, and here
   connect to an in-memory database.

### Querying

Now, let's do a query! By default, `PRQLMagic` always returns the results as
dataframe, and always prints the results. The results of the previous query are
accessible in the `_` variable.

These examples are based on the `products.csv` example above.

```


In [4]: %%prql
   ...: from p = products.csv
   ...: filter supplierID == 1

Done.
Returning data to local variable _
   productID    productName  supplierID  categoryID      quantityPerUnit  unitPrice  unitsInStock  unitsOnOrder  reorderLevel  discontinued
0          1           Chai           1           1   10 boxes x 20 bags       18.0            39             0            10             0
1          2          Chang           1           1   24 - 12 oz bottles       19.0            17            40            25             0
2          3  Aniseed Syrup           1           2  12 - 550 ml bottles       10.0            13            70            25             0
```

```
In [5]: %%prql
   ...: from p = products.csv
   ...: group categoryID (
   ...:   aggregate [average unitPrice]
   ...: )

Done.
Returning data to local variable _
   categoryID  avg("unitPrice")
0           1         37.979167
1           2         23.062500
2           7         32.370000
3           6         54.006667
4           8         20.682500
5           4         28.730000
6           3         25.160000
7           5         20.250000
```

We can capture the results into a different variable like so:

```
In [6]: %%prql results <<
   ...: from p = products.csv
   ...: aggregate [min unitsInStock, max unitsInStock]

Done.
Returning data to local variable results
   min("unitsInStock")  max("unitsInStock")
0                    0                  125
```

Now, the output of the query is saved to `results`.

:::{Note}

Unlike `IPython-SQL`, we currently only support queries in a cell magic (i.e.
`%%prql`), and not a line magic (i.e. `%prql`). So the following will **not**
work:

```
In [4]: %prql from data | select freq
```

This mainly to work around some parsing challenges,
and it may be added as a feature in a future release.
:::

## Configuration

We strive to provide sane defaults;
however,
should you need to change settings,
a list of settings is available using the `%config` line magic.

```
In [7]: %config PRQLMagic
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

```
In [7]: %config PRQLMagic.autoview = False
```

[jupysql]: https://github.com/ploomber/jupysql
[conn_str]: https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls
[duckdb]: https://duckdb.org
[pandas]: https://pandas.pydata.org
