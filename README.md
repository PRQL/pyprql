# PyPrql

Python implementation of [PRQL](https://github.com/max-sixty/prql).

Documentation of PRQL is at https://github.com/max-sixty/prql

### Installation
```
    pip install pyprql
```

## CLI

Usage:

```bash
    pyprql 'connection_string'
    pyprql 'postgresql://user:password@localhost:5432/database'    
```
Examples:

```bash
    pyprql 'sqlite:///chinook.db'
```
Try it out:

```
curl https://github.com/qorrect/PyPrql/blob/main/resources/chinook.db?raw=true -o chinook.db 
pyprql "sqlite:///chinook.db"

PRQL> show tables 
```

## pyprql.to_sql 

```elm
query='''
from employees
filter country = "USA"
derive [
  gross_salary: salary + payroll_tax,
  gross_cost:   gross_salary + benefits_cost
]
filter gross_cost > 0
aggregate by:[title, country] [
    average salary,
    sum     salary,
    average gross_salary,
    sum     gross_salary,
    average gross_cost,
    sum_gross_cost: sum gross_cost,
    row_count: count salary
]
sort sum_gross_cost
filter row_count > 200
take 20
'''
```

---

```python

from pyprql import to_sql
sql = to_sql(query)
print(sql)
```

---

```sql
SELECT AVG(salary),
       SUM(salary),
       AVG(salary + payroll_tax),
       SUM(salary + payroll_tax),
       AVG(salary + payroll_tax + benefits_cost),
       SUM(salary + payroll_tax + benefits_cost) as sum_gross_cost,
       COUNT(salary)                             as row_count,
       salary + payroll_tax                      as gross_salary,
       (salary + payroll_tax) + benefits_cost    as gross_cost
FROM `employees` employees_e
WHERE country="USA" AND (gross_salary+benefits_cost)>0
GROUP BY title, country
HAVING row_count >200
ORDER BY sum_gross_cost
LIMIT 20

```

#### Differences from the spec

The parser is only able to parse casts in select statements insde of `[ ]`, so

```sql
select foo | as float
```

will fail, it must be wrapped in brackets as a single item list.

```sql
select [ foo | as float ]
```
