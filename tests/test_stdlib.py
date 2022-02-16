import sqlite3
import unittest

import prql


class TestStdlib(unittest.TestCase):
    def setUp(self) -> None:
        db_path = f'./employee.db'
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

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

    def test_std_lib_min(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate [
            min_price: price | min     
        ]

        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('MIN(price)') != -1)
        self.run_query(q, 1)
        print(res)

    def test_stdlib_max(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate max_price: price | max     
    
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('MAX(price)') != -1)
        self.run_query(q, 1)
        print(res)

    def test_stdlib_count(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate foo | count      

        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('COUNT(foo)') != -1)
        self.run_query(q, 1)
        print(res)

    def test_stdlib_count(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate count  
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('COUNT(*)') != -1)
        self.run_query(q, 1)
        print(res)
