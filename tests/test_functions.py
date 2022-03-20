# -*- coding: utf-8 -*-
import sqlite3
import unittest
from pathlib import Path

from pyprql.lang import prql


class TestSqlGenerator(unittest.TestCase):
    def setUpClass() -> None:
        # Use Path for robust construction, but sqlite3 py3.6 requires str
        db_path = str(Path("tests", "../resources/employee.db"))
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
            assert len(rows) == expected

    def test_select_all(self):
        q = """
        func no_params = s"COUNT(*)"
        from table
        select foo
        aggregate [
            cnt: no_params
        ]
        """
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index("COUNT(*) as cnt") > 0)
        self.run_query(q)

    def test_replace_function(self):
        q = """
        from table
        select name
        derive cleaned: name | replace "foo" "bar"

        """
        res = prql.to_sql(q)
        self.assertTrue(res.index('REPLACE(name,"foo","bar") as cleaned') > 0)
        print(res)
        self.run_query(q, 12)

    def test_nested_functions(self):
        q = """from table
        select name
        derive [
            trimmed: name | rtrim ,
            cleaned: name | replace "dirty" "clean",
            nested: (name | rtrim ",") | ltrim,
            triple_nested: ((name | replace "dirty" "clean") | replace "," " ") | trim " "
        ]"""
        res = prql.to_sql(q)
        print(res)
        trimmed = "RTRIM(name) as trimmed"
        simple = 'REPLACE(name,"dirty","clean") as cleaned'
        nest1 = 'LTRIM(RTRIM(name,",")) as nested'
        triple = (
            'TRIM(REPLACE(REPLACE(name,"dirty","clean"),","," ")," ") as triple_nested'
        )
        self.assertTrue(res.index(trimmed) != -1)
        self.assertTrue(res.index(simple) != -1)
        self.assertTrue(res.index(nest1) != -1)
        self.assertTrue(res.index(triple) != -1)
        self.run_query(q, 12)
