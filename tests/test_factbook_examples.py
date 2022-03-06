import sqlite3
import unittest

import prql


class TestSQLGeneratorForFactbook(unittest.TestCase):

    def setUpClass() -> None:
        db_path = f'./factbook.db'
        TestSQLGeneratorForFactbook.con = sqlite3.connect(db_path)
        TestSQLGeneratorForFactbook.cur = TestSQLGeneratorForFactbook.con.cursor()

    def run_query(self, text, expected):
        print(text.replace('\n\n', '\n'))
        print('-' * 40)
        sql = prql.to_sql(text)
        print(sql)
        rows = TestSQLGeneratorForFactbook.cur.execute(sql)
        columns = [d[0] for d in rows.description]
        print(f'Columns: {columns}')
        rows = rows.fetchall()
        assert (len(rows) == expected)

    def test_factbook_q1(self):
        # SELECT * FROM facts LIMIT 1;
        text = 'from facts | take 1'
        self.run_query(text, 1)

    def test_factbook_q2(self):
        text = '''
        # SELECT name, area_land - area_water as just_land FROM facts LIMIT 2
        from facts | select name | derive [ just_land: area_land - area_water ]  | take 2
        '''
        self.run_query(text, 2)

    def test_factbook_q3(self):
        text = '''
        #SELECT name
        #FROM facts
        #WHERE population = (SELECT MIN(population) FROM facts);
        
        func  min_value column table = (
            s"(SELECT MIN({column}) FROM {table})"
        )
        
        from facts
        select name
        filter population = population | min_value facts
        take 3
        '''
        self.run_query(text, 1)

    def test_factbook_q3b(self):
        text = '''
        
        value min_pop = (
            from facts
            aggregate min population
            take 1
        )
        from facts
        select name
        filter population = min_pop
        '''

        self.run_query(text, 1)

    def test_factbook_q4(self):
        # # SELECT * FROM cities JOIN facts  ON cities.facts_id = facts.id LIMIT 15
        text = 'from cities | join facts [facts_id=id] | take 4'
        self.run_query(text, 4)

    def test_factbook_q5(self):
        text = '''
        #SELECT cities.name            as city,
        #       facts.name             as country,
        #       SUM(facts.population)  as country_pop,
        #       SUM(cities.population) as city_pop
        #FROM facts
        #         INNER JOIN cities on cities.facts_id = facts.id
        #GROUP BY code
        #ORDER BY city_pop DESC
        #LIMIT 15
        
        from facts
        join cities [id=facts_id]
        derive [
            city: "cities.name",
            country: "facts.name"
        ]
        aggregate by:[code] [
            country_pop: sum facts.population,
            city_pop: cities.population | sum
        ]
        sort "city_pop desc"
        take 5        
        
        '''
        self.run_query(text, 5)

    def test_factbook_q6(self):
        text = '''
        #SELECT cities.name            as city,
        #       facts.name             as country,
        #       facts.area             as country_area,
        #       facts.birth_rate - facts.death_rate as population_growth,
        #       SUM(facts.population)  as country_pop,
        #       SUM(cities.population) as city_pop
        #FROM facts
        #         INNER JOIN cities on cities.facts_id = facts.id
        #GROUP BY code
        #ORDER BY city_pop DESC
        #LIMIT 15
        
        
        from facts
        join cities [id=facts_id]
        derive [
            city: "cities.name",
            country: "facts.name",
            country_area: "facts.area",
            population_growth: "facts.birth_rate - facts.death_rate",
        ]
        aggregate by:code [
            country_pop: "SUM(facts.population)",
            city_pop: "SUM(cities.population)"
        ]
        sort "city_pop desc"
        take 6
        '''
        self.run_query(text, 6)


if __name__ == '__main__':
    unittest.main()
