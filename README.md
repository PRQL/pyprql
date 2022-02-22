# PyPrql

Python implementation of [PRQL](https://github.com/max-sixty/prql).

Documentation of PRQL is at https://github.com/max-sixty/prql

```elm
from facts
join cities [id=facts_id]
derive [
   city: "cities.name",
   country: "facts.name"
]
aggregate by:code [
   country_pop: sum facts.population,
   city_pop: cities.population | sum
]
sort "city_pop desc"
take 5   
```
---

```python

import prql
sql = prql.to_sql(q)
print(sql)
```

---

```sql
SELECT SUM(facts_f.population)  as country_pop,
       SUM(cities_c.population) as city_pop,
       "cities_c.name"          as city,
       "facts_f.name"           as country
FROM ` facts ` facts_f JOIN cities cities_c
ON facts_f.id = cities_c.facts_id
WHERE 1=1
GROUP BY code
ORDER BY "city_pop desc"
LIMIT 5

```

### Differences from the spec

The parser is only able to parse casts in select statements insde of `[ ]`, so

```sql
select foo | as float
```

will fail, it must be wrapped in brackets as a single item list.

```sql
select [ foo | as float ]
```

