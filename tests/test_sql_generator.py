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

    def test_join_syntax(self):
        q = '''
        from table
        join table2 [id=id]
        '''
        res = prql.to_sql(q)
        self.assertTrue(res.index('JOIN table2 table2_t ON table_t.id = table2_t.id') != -1)

    def test_join_syntax_2(self):
        q = '''
        from table
        join table2 [table.id=table2.id]
        '''
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('JOIN table2 table2_t ON table_t.id = table2_t.id') != -1)

    def test_group_by_single_item_array(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate by:[code] [
            sum price 
        ] 
        '''
        res = prql.to_sql(q)

        self.assertTrue(res.index('sum(price) as sum_price') != -1)
        self.assertTrue(res.index('GROUP BY code') != -1)

    def test_group_by_double_item_array(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate by:[code,country] [
            sum price 
        ] 
        '''
        res = prql.to_sql(q)

        self.assertTrue(res.index('sum(price) as sum_price') != -1)
        self.assertTrue(res.index('GROUP BY code,country') != -1)

    def test_groupby_single_argument(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate by:code [
            sum price 
        ] 
        '''
        res = prql.to_sql(q)

        self.assertTrue(res.index('sum(price) as sum_price') != -1)
        self.assertTrue(res.index('GROUP BY code') != -1)

    def test_named_aggs(self):
        q = '''
        from table
        select [ foo, bar ]
        aggregate by:code [
            all_costs: sum price 
        ] 
        '''
        res = prql.to_sql(q)

        self.assertTrue(res.index('sum(price) as all_costs') != -1)
        self.assertTrue(res.index('GROUP BY code') != -1)


    def test_derive_syntax(self):
        q = '''
        from table
        derive [
         foo_bar: foo + bar
        ]
        '''
        res = prql.to_sql(q)
        print(res)