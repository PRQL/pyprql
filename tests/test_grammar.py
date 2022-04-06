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

    def test_expressions_in_filter(self):
        # Songs greater than 5 minutes

        q = '''
        from t:tracks
        select t.Composer
        filter t.Milliseconds * 1000 > 5 * 60
        '''
        res = prql.to_sql(q)
        print(res)


