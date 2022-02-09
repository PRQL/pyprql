SELECT cities.name            as city,
       facts.name             as country,
       facts.area             as country_area,
       facts.birth_rate - facts.death_rate as population_growth,
       SUM(facts.population)  as country_pop,
       SUM(cities.population) as city_pop
FROM facts
         INNER JOIN cities on cities.facts_id = facts.id
GROUP BY code
ORDER BY city_pop DESC
LIMIT 15
