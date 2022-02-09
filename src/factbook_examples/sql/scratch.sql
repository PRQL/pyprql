SELECT cities.name as capital,
       facts.name as country,
       cities.population as city_pop,
       facts.population as country_pop,
       CAST(cities.population as float) / CAST(facts.population as float) as city_size
from cities
         LEFT JOIN facts on cities.facts_id = facts.id
where capital = 1
