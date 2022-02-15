import sqlite3
import unittest

import prql


class TestEmployeeExamples(unittest.TestCase):
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

    def test_index(self):
        q =  '''
        from employees
        filter country = "USA"                           # Each line transforms the previous result.
        derive [                                         # This adds columns / variables.
          gross_salary: salary + payroll_tax,
          gross_cost:   gross_salary + benefits_cost     # Variables can use other variables.
        ]
        filter gross_cost > 0
        aggregate by:[title, country] [                  # `by` are the columns to group by.
            average salary,                              # These are aggregation calcs run on each group.
            sum     salary,
            average gross_salary,
            sum     gross_salary,
            average gross_cost,
            sum_gross_cost: sum gross_cost,
            count
        ]
        sort sum_gross_cost
        filter count > 200
        take 20
        '''
        # self.run_query(q)


    def test_cte1(self):
        text= '''
        table newest_employees = (
            from employees
            sort tenure
            take 50
        )
        
        from newest_employees
        join salary [id]
        select [name, salary]
        '''
        # self.run_query(text)