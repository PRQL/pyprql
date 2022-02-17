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

    def test_stdlib_sum(self):
        q = '''from table | select foo | aggregate sum foo'''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('SUM(foo)') != -1)
        self.run_query(q, 1)
        print(res)

    def test_stdlib_sum_2(self):
        q = '''from table | select foo | aggregate foo | sum '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('SUM(foo)') != -1)
        self.run_query(q, 1)
        print(res)

    def test_stdlib_sum_3(self):
        q = '''from table | select foo | aggregate hey_its_here: foo | sum '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('SUM(foo) as hey_its_here') != -1)
        self.run_query(q, 1)
        print(res)

    def test_stdlib_avg(self):
        q = '''from table | select foo | aggregate foo | avg'''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('AVG(foo)') != -1)
        self.run_query(q, 1)
        print(res)

    def test_stdlib_stddev(self):
        q = '''from table | select foo | aggregate foo | stddev'''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('STDDEV(foo)') != -1)
        # self.run_query(q, 1)
        # print(res)

    def test_stdlib_avg2(self):
        q = '''from table | select foo | aggregate my_foo: foo | avg'''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('AVG(foo) as my_foo') != -1)
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

    def test_stdlib_count_2(self):
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

    def test_stdlib_count_distinct(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate foo | count_distinct  
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('COUNT(DISTINCT `foo`)') != -1)
        self.run_query(q, 1)
        print(res)

    def test_casts(self):
        q = '''
        from table
        select [foo | as float]
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('CAST(foo as float)') != -1)
        self.run_query(q, 12)
        print(res)

    def test_casts_float(self):
        q = '''
        from table | select [foo | as float, bar] | take 5 
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('CAST(foo as float)') != -1)
        self.run_query(q, 5)
        print(res)

    def test_casts_string(self):
        q = '''
        from table | select [foo | as string, bar] | take 5 
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('CAST(foo as string)') != -1)
        self.run_query(q, 5)
        print(res)

    def test_casts_date(self):
        q = '''
        from table | select [foo | as date, bar] | take 5 
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('CAST(foo as date)') != -1)
        self.run_query(q, 5)
        print(res)

    def test_casts_datetime(self):
        q = '''
        from table | select [foo | as datetime, bar] | take 5 
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('CAST(foo as datetime)') != -1)
        self.run_query(q, 5)
        print(res)

    def test_casts_time(self):
        q = '''
        from table | select [foo | as time, bar] | take 5 
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('CAST(foo as time)') != -1)
        self.run_query(q, 5)
        print(res)

    def test_casts_double(self):
        q = '''
        from table | select [foo | as double, bar] | take 5 
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('CAST(foo as double)') != -1)
        self.run_query(q, 5)
        print(res)
