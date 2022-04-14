# PyPrql

Python implementation of [PRQL](https://github.com/prql/prql).

Documentation of PRQL is at https://lang.prql.builders/introduction.html

## Installation
```
    pip install pyprql
```

### Try it out

##### Database
```
curl https://github.com/qorrect/PyPrql/blob/main/resources/chinook.db?raw=true -o chinook.db 
pyprql "sqlite:///chinook.db"

PRQL> show tables 
```
##### CSV file
```
curl https://people.sc.fsu.edu/~jburkardt/data/csv/zillow.csv
pyprql zillow.csv 
```
### The pyprql tool 

* pyprql can connect to any database that SQLAlchemy supports, execute `pyprql` without arguments for how to install drivers.
* pyprql also supports CSV files, simply replace the connection string with the file path and it will load the CSV into a temporary SQLite database
* pyprql can save the results with a ` | to csv ${filename}` transform at the end of the query  
* pyprql has auto-completion on table names and table aliases with _tab_, as well as history-completion with _alt-f_
