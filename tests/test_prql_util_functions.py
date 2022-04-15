# -*- coding: utf-8 -*-
"""Tests on the Factbook database."""
import unittest

import pandas as pd

from pyprql.cli.cli import clean_column_names
from pyprql.lang import prql


class TestSQLGeneratorForFactbook(unittest.TestCase):
    """A unittest.TestCase."""

    def test_clean_columns(self):
        """Clean column names correctly."""
        data = {
            '"age"': [32, 45],
            "sex of human": ["M", "F"],
            "color_(rgb)": ["W", "B"],
        }
        df = pd.DataFrame.from_dict(data)
        print("\n")
        print(df)
        df.columns = clean_column_names(df)

        assert df.columns[0].find('"') == -1
        assert df.columns[0] == "age"

        assert df.columns[1].find(" ") == -1
        assert df.columns[1] == "sex_of_human"

        assert df.columns[2].find("(") == -1
        assert df.columns[2].find(")") == -1

    def test_get_operations(self):
        """Retrieve operations correctly."""
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
