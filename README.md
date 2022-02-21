# PyPrql

Python implementation of [PRQL](https://github.com/max-sixty/prql).

```python

import prql

q = "from cities | join facts [facts_id=id] | take 15"
sql = prql.to_sql(q)
print(sql)
```

---

```sql
SELECT *
FROM cities
         JOIN facts ON cities.facts_id = facts.id
LIMIT 15
```

### Differences from the spec

The parser is only able to parse float casts in select statements insde of `[ ]`, so

```sql
select foo | as float
```

will fail, it must be wrapped in brackets as a single item array.

```sql
select [ foo | as float ]
```

