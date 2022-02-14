# PyPrql
Python implementation of [PRQL](https://github.com/max-sixty/prql). 

```python

import prql

q = """
from employees
filter country = "USA"                           # Each line transforms the previous result.
derive [                                         # This adds columns / variables.
  gross_salary: salary + payroll_tax,
  gross_cost:   gross_salary + benefits_cost     # Variables can use other variables.
]
filter gross_cost > 0
aggregate by:[title, country] [                  # `by` are the columns to group by.
    average salary,                              # These are aggregation calcs run on each group.
    sum     salary,
    average gross_salary,
    sum     gross_salary,
    average gross_cost,
    sum_gross_cost: sum gross_cost,
    count
]
sort sum_gross_cost
filter count > 200
take 20
"""

sql = prql.to_sql(q)
print(sql)
```

--- 

```sql
SELECT average(salary)              as average_salary,
       sum(salary)                  as sum_salary,
       average(gross_salary)        as average_gross_salary,
       sum(gross_salary)            as sum_gross_salary,
       average(gross_cost)          as average_gross_cost,
       sum(gross_cost)              as sum_gross_cost,
       salary + payroll_tax         as gross_salary,
       gross_salary + benefits_cost as gross_cost
FROM employees ele
WHERE country = USA
  AND gross_cost > 0
  AND count > 200
GROUP BY title, country LIMIT 20

```

