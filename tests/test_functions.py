# -*- coding: utf-8 -*-
"""Tests for statements."""
import sqlite3
import unittest
from pathlib import Path

from pyprql.lang import prql


class TestSqlGenerator(unittest.TestCase):
    """A unittest.TestCase."""

    @classmethod
    def setUpClass(cls) -> None:
        """Setup tests."""
        # Use Path for robust construction, but sqlite3 py3.6 requires str
        db_path = str(Path("tests", "../resources/employee.db"))
        cls.con = sqlite3.connect(db_path)  # type:ignore[attr-defined]
        cls.cur = cls.con.cursor()  # type:ignore[attr-defined]

    def run_query(self, text, expected=None):
        """Run a query."""
        # print(text.replace('\n\n', '\n'))
        # print('-' * 40)
        sql = prql.to_sql(text)
        # print(sql)
        rows = self.cur.execute(sql)
        _ = [d[0] for d in rows.description]
        # print(f'Columns: {columns}')
        rows = rows.fetchall()
        if expected is not None:
            assert len(rows) == expected

    def test_select_all(self):
        """Select all columns."""
        q = """
        func no_params = s"COUNT(*)"
        from table
        select foo
        aggregate [
            cnt: no_params
        ]
        """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("COUNT(*) as cnt") > 0)
        self.run_query(q)

    def test_replace_function(self):
        """Replace strings in a column."""
        q = """
        from table
        select name
        derive cleaned: name | replace "foo" "bar"

        """
        res = prql.to_sql(q)
        self.assertTrue(res.index('REPLACE(name,"foo","bar") as cleaned') > 0)
        # print(res)
        self.run_query(q, 12)

    def test_nested_functions(self):
        """Evaulate nested functions."""
        q = """from table
        select name
        derive [
            trimmed: name | rtrim ,
            cleaned: name | replace "dirty" "clean",
            nested: (name | rtrim ",") | ltrim,
            triple_nested: ((name | replace "dirty" "clean") | replace "," " ") | trim " "
        ]"""
        res = prql.to_sql(q)
        # print(res)
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
