# -*- coding: utf-8 -*-
import unittest

from pyprql.lang import prql


class TestSQLGeneratorForFactbook(unittest.TestCase):
    def test_get_operations(self):
        text = """
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
                    row_count: count salary
                ]
                sort sum_gross_cost
                filter row_count > 200
                take 20"""

        ast = prql.parse(text)

        # First get all derives
        all_filters = prql.get_operation(
            ast.get_from().pipes.operations, prql.Filter, return_all=True
        )
        self.assertTrue(len(all_filters) == 3)

        wheres = prql.get_operation(
            ast.get_from().pipes.operations,
            prql.Filter,
            return_all=True,
            before=prql.Aggregate,
        )

        self.assertTrue(len(wheres) == 2)

        havings = prql.get_operation(
            ast.get_from().pipes.operations,
            prql.Filter,
            return_all=True,
            after=prql.Aggregate,
        )

        self.assertTrue(len(havings) == 1)
