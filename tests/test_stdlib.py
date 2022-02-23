import sqlite3
import unittest

import prql


class TestStdlib(unittest.TestCase):
    def setUpClass() -> None:
        db_path = f'./employee.db'
        TestStdlib.con = sqlite3.connect(db_path)
        TestStdlib.cur = TestStdlib.con.cursor()

    def run_query(self, text, expected=None):
        # print(text.replace('\n\n', '\n'))
        # print('-' * 40)
        sql = prql.to_sql(text)
        # print(sql)
        rows = TestStdlib.cur.execute(sql)
        columns = [d[0] for d in rows.description]
        # print(f'Columns: {columns}')
        rows = rows.fetchall()
        if expected is not None:
            assert (len(rows) == expected)

    def test_min(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate [
            min_price: price | min     
        ]'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('MIN(price)') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_max(self):
        q = '''
        from table | select [ foo, bar ] | aggregate max_price: price | max '''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('MAX(price)') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_sum(self):
        q = '''from table | select foo | aggregate sum foo'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('SUM(foo)') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_sum_2(self):
        q = '''from table | select foo | aggregate foo | sum '''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('SUM(foo)') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_sum_3(self):
        q = '''from table | select foo | aggregate hey_its_here: foo | sum '''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('SUM(foo) as hey_its_here') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_avg(self):
        q = '''from table | select foo | aggregate foo | avg'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('AVG(foo)') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_stddev(self):
        q = '''from table | select foo | aggregate foo | stddev'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('STDDEV(foo)') != -1)
        # self.run_query(q, 1)
        # #print(res)

    def test_avg2(self):
        q = '''from table | select foo | aggregate my_foo: foo | avg'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('AVG(foo) as my_foo') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_count(self):
        q = '''from table | select [ foo, bar ] | aggregate foo | count'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('COUNT(foo)') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_count_2(self):
        q = '''
        from table | select [ foo, bar ] | aggregate count'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('COUNT(*)') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_count_distinct(self):
        q = '''
        from table | select [ foo, bar ] | aggregate foo | count_distinct foo'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('COUNT(DISTINCT `foo`)') != -1)
        self.run_query(q, 1)
        # print(res)

    def test_casts(self):
        q = '''
        from table | select [foo | as float]'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('CAST(foo as float)') != -1)
        self.run_query(q, 12)
        # print(res)

    def test_casts_float(self):
        q = '''
        from table | select [foo | as float, bar] | take 5'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('CAST(foo as float)') != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_string(self):
        q = '''
        from table | select [foo | as string, bar] | take 5'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('CAST(foo as string)') != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_date(self):
        q = '''
        from table | select [foo | as date, bar] | take 5'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('CAST(foo as date)') != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_datetime(self):
        q = '''
        from table | select [foo | as datetime, bar] | take 5'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('CAST(foo as datetime)') != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_time(self):
        q = '''
        from table | select [foo | as time, bar] | take 5 '''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('CAST(foo as time)') != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_double(self):
        q = '''
        from table | select [foo | as double, bar] | take 5'''
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('CAST(foo as double)') != -1)
        self.run_query(q, 5)
        # print(res)

    def test_unknown_function(self):
        q = 'from table | select name  | derive capitalized: name | topper | take 5'
        try:
            res = prql.to_sql(q)
            self.assertTrue(False)
        except prql.PRQLException as e:
            print(e, repr(e))
            self.assertTrue(True)
            self.assertTrue(str(e).index('Unknown function') != -1)
        # print(res)

    def test_upper(self):
        q = 'from table | select name  | derive capitalized: name | upper | take 5'
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('UPPER(name)') != -1)
        self.run_query(q, 5)

    def test_trim(self):
        q = 'from table | select name  | derive trimmed: name | trim | take 5'
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('TRIM(name)') != -1)
        self.run_query(q, 5)
        self.assertTrue(False)

    def test_trim_with_args(self):
        self.assertTrue(False)

    def test_ltrim(self):
        self.assertTrue(False)

    def test_ltrim_with_args(self):
        self.assertTrue(False)

    def test_rtrim(self):
        self.assertTrue(False)

    def test_rtrim_with_args(self):
        self.assertTrue(False)

    def test_replace(self):
        self.assertTrue(False)

    def substr(self):
        self.assertTrue(False)
