import sqlite3
import unittest

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
        func no_params = f"COUNT(*)"
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
