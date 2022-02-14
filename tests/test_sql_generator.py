import unittest

import prql


class TestSqlGenerator(unittest.TestCase):

    def test_select_all(self):
        q = '''
        from table
        '''
        res = prql.to_sql(q)
        self.assertTrue(res.startswith('SELECT * FROM table'))

    def test_limit(self):
        q = 'from table | take 10'
        res = prql.to_sql(q)
        self.assertTrue(res.index('LIMIT 10') != -1)

    def test_order_by(self):
        q = 'from table | sort name'
        res = prql.to_sql(q)
        self.assertTrue(res.index('ORDER BY name') != -1)

    def test_order_by_desc(self):
        pass # FAIL

    def test_join_syntax(self):
        q = '''
        from table
        join table2 [id1=id2]
        '''
        res = prql.to_sql(q)
        self.assertTrue(res.index('JOIN table2 table2_t ON table_t.id1 = table2_t.id2') != -1)

    def test_agg_syntax(self):
        q = '''
        from table
        select [ foo, bar ] 
        '''