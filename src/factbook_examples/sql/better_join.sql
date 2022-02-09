SELECT cities.name            as city,
       facts.name             as country,
       SUM(facts.population)  as country_pop,
       SUM(cities.population) as city_pop
FROM facts
         INNER JOIN cities on cities.facts_id = facts.id
GROUP BY code
ORDER BY city_pop DESC
LIMIT 15