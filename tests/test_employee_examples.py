import sqlite3
import unittest

import prql


class TestEmployeeExamples(unittest.TestCase):
    def setUp(self) -> None:
        self.base_path = 'employee_examples'
        db_path = f'./{self.base_path}/employee.db'
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()
    def get_query(self, file_name):
        return prql.read_file('/../tests/' + self.base_path + '/' + file_name)

    def run_query(self, text, expected=None):
        print(text.replace('\n\n', '\n'))
        print('-' * 40)
        sql = prql.to_sql(text)
        print(sql)
        rows = self.cur.execute(sql)
        columns = [d[0] for d in rows.description]
        print(f'Columns: {columns}')
        rows = rows.fetchall()
        if expected is not None:
            assert (len(rows) == expected)

    def test_index(self):
        q = self.get_query('index.prql')
        # self.run_query(q)

