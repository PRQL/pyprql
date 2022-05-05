# -*- coding: utf-8 -*-
"""Unit tests for prql_python compatibility."""
import prql_python as prql


def test_pyql_python():
    """It compiles sql from prql."""
    sql = prql.to_sql("from employees | select [ name, age ]")
    print(sql)
