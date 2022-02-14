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
SELECT  SUM(fcs.population) as country_pop,SUM(cte.population) as city_pop ,cte.name  as city ,fcs.name  as country ,fcs.area  as country_area ,fcs.birth_rate - fcs.death_rate  as population_growth  FROM facts fcs JOIN cities cte ON fcs.id = cte.facts_id WHERE 1=1 GROUP BY code  LIMIT 6

```

