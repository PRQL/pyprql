import sqlite3
import unittest

from prql import parse, read_file, prql_to_sql


class TestSQLGenerator(unittest.TestCase):

    def setUp(self) -> None:
        self.base_path = 'factbook_examples'
        db_path = f'./{self.base_path}/factbook.db'
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

    def get_query(self, file_name):
        return read_file('/../tests/' + self.base_path + '/' + file_name)

    def test_factbook_q1(self):
        text = self.get_query('q1.prql')
        self.run_query(text, 1)

    def run_query(self, text, expected):
        print(text.replace('\n\n', '\n'))
        print('-' * 40)
        tree = parse(text)
        sql = prql_to_sql(tree._from, tree, verbose=False)
        print(sql)
        rows = self.cur.execute(sql)
        columns = [d[0] for d in rows.description]
        print(f'Columns: {columns}')
        rows = rows.fetchall()
        assert (len(rows) == expected)

    def test_factbook_q2(self):
        text = self.get_query('q2.prql')
        self.run_query(text, 2)

    def test_factbook_q3(self):
        text = self.get_query('q3.prql')
        self.run_query(text, 3)


if __name__ == '__main__':
    unittest.main()
