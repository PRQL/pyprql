import sqlite3
import unittest

import pytest

import prql


class TestSqlGenerator(unittest.TestCase):

    def setUpClass() -> None:
        db_path = f'./employee.db'
        TestSqlGenerator.con = sqlite3.connect(db_path)
        TestSqlGenerator.cur = TestSqlGenerator.con.cursor()

    def run_query(self, text, expected=None):
        # print(text.replace('\n\n', '\n'))
        # print('-' * 40)
        sql = prql.to_sql(text)
        # print(sql)
        rows = TestSqlGenerator.cur.execute(sql)
        columns = [d[0] for d in rows.description]
        # print(f'Columns: {columns}')
        rows = rows.fetchall()
        if expected is not None:
            assert (len(rows) == expected)

    def test_select_all(self):
        q = '''
        func no_params = s"COUNT(*)"
        from table
        select foo
        aggregate [
            cnt: no_params
        ]
        '''
        res = prql.to_sql(q)
        print(res)
        # self.assertTrue(res.startswith('SELECT * FROM `table`'))
        self.run_query(q)

    def test_replace_function(self):
        q = '''
        from table 
        select name 
        derive cleaned: name | replace "foo" "bar"
        
        '''
        res = prql.to_sql(q)
        print(res)

    def test_nested_functions(self):
        q = '''from table
        select name
        derive [ 
            trimmed: name | rtrim ,
            cleaned: name | replace "dirty" "clean",
            nested: (name | rtrim ",") | ltrim,
            triplenested: ((name | replace "dirty" "clean") | replace "," " ") | trim " "
        ]'''
        res = prql.to_sql(q)
        simple = 'REPLACE(name,"dirty","clean") as cleaned'
        nest1 = 'LTRIM(RTRIM(name,",")) as nested'
        triple = 'TRIM(REPLACE(REPLACE(name,"dirty","clean"),","," ")," ") as triplenested'
        self.assertTrue(res.index(simple) != -1)
        self.assertTrue(res.index(nest1) != -1)
        self.assertTrue(res.index(triple) != -1)
        self.run_query(q, 12)
