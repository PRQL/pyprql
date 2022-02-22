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
