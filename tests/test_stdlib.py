# -*- coding: utf-8 -*-
"""Tests for the Std. Lib."""
import sqlite3
import unittest
from pathlib import Path

import pytest

from pyprql.lang import prql


class TestStdlib(unittest.TestCase):
    """A unittest.TestCase."""

    @classmethod
    def setUpClass(cls) -> None:
        """Setup the tests."""
        # Use Path for robust construction, but sqlite3 py3.6 requires str
        db_path = str(Path("tests", "../resources/employee.db"))
        cls.con = sqlite3.connect(db_path)  # type:ignore[attr-defined]
        cls.cur = cls.con.cursor()  # type:ignore[attr-defined]

    def run_query(self, text, expected=None):
        """Run a query."""
        # print(text.replace('\n\n', '\n'))
        # print('-' * 40)
        sql = prql.to_sql(text)
        # print(sql)
        rows = self.cur.execute(sql)
        _ = [d[0] for d in rows.description]
        # print(f'Columns: {columns}')
        rows = rows.fetchall()
        if expected is not None:
            assert len(rows) == expected

    def test_min(self):
        """Find minimums correctly."""
        q = """
        from table
        select [ foo, bar ]
        aggregate [
            min_price: price | min
        ]"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("MIN(price)") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_max(self):
        """Find maximums correctly."""
        q = """
        from table | select [ foo, bar ] | aggregate max_price: price | max """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("MAX(price)") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_sum(self):
        """Find sums correctly."""
        q = """from table | select foo | aggregate sum foo"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("SUM(foo)") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_sum_2(self):
        """Find piped sums correctly."""
        q = """from table | select foo | aggregate foo | sum """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("SUM(foo)") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_sum_3(self):
        """Find find piped sums in aggregate bodies correctly."""
        q = """from table | select foo | aggregate hey_its_here: foo | sum """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("SUM(foo) as hey_its_here") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_avg(self):
        """Find averages in aggregate body correctly."""
        q = """from table | select foo | aggregate [average_foo: foo | avg]"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("AVG(foo)") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_avg2(self):
        """Find piped averages correctly."""
        q = """from table | select foo | aggregate my_foo: foo | avg"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("AVG(foo) as my_foo") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_stddev(self):
        """Find standard deviations correctly."""
        q = """from table | select foo | aggregate foo | stddev"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("STDDEV(foo)") != -1)
        # self.run_query(q, 1)
        # #print(res)

    def test_count(self):
        """Find piped counts correctly."""
        q = """from table | select [ foo, bar ] | aggregate foo | count"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("COUNT(foo)") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_count_2(self):
        """Find counts in aggregate body correctly."""
        q = """
        from table | select [ foo, bar ] | aggregate count"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("COUNT(*)") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_count_distinct(self):
        """Find count_distinct correctly."""
        q = """
        from table | select [ foo, bar ] | aggregate foo | count_distinct foo"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("COUNT(DISTINCT `foo`)") != -1)
        self.run_query(q, 1)
        # print(res)

    def test_casts(self):
        """Cast columns correctly."""
        q = """
        from table | select [foo | as float]"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("CAST(foo as float)") != -1)
        self.run_query(q, 12)
        # print(res)

    def test_casts_float(self):
        """Cast columns as floats in select body correctly."""
        q = """
        from table | select [foo | as float, bar] | take 5"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("CAST(foo as float)") != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_string(self):
        """Cast columns as strings in select body correctly."""
        q = """
        from table | select [foo | as string, bar] | take 5"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("CAST(foo as string)") != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_date(self):
        """Cast columns as dates in select body correctly."""
        q = """
        from table | select [foo | as date, bar] | take 5"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("CAST(foo as date)") != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_datetime(self):
        """Cast columns as datetimes in select body correctly."""
        q = """
        from table | select [foo | as datetime, bar] | take 5"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("CAST(foo as datetime)") != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_time(self):
        """Cast columns as times in select body correctly."""
        q = """
        from table | select [foo | as time, bar] | take 5 """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("CAST(foo as time)") != -1)
        self.run_query(q, 5)
        # print(res)

    def test_casts_double(self):
        """Cast columns as doules in select body correctly."""
        q = """
        from table | select [foo | as double, bar] | take 5"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("CAST(foo as double)") != -1)
        self.run_query(q, 5)
        # print(res)

    def test_unknown_function(self):
        """Throw error on unknown function."""
        q = "from table | select name  | derive capitalized: name | topper | take 5"
        try:
            res = prql.to_sql(q)
            self.assertTrue(False)
        except prql.PRQLException as e:
            print(e, repr(e))
            self.assertTrue(True)
            self.assertTrue(str(e).index("Unknown function") != -1)
        # print(res)

    def test_upper(self):
        """Capitalise strings correctly."""
        q = "from table | select name  | derive capitalized: name | upper | take 5"
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("UPPER(name) as capitalized") != -1)
        self.run_query(q, 5)

    def test_trim(self):
        """Trim strings correctly."""
        q = "from table | select name  | derive trimmed: name | trim | take 5"
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("TRIM(name) as trimmed") != -1)
        self.run_query(q, 5)

    def test_trim_with_args(self):
        """Trim strings with arguments correctly."""
        q = """from table
            select name
            derive [ trimmed: name | trim "," ]
        """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('TRIM(name,",") as trimmed') != -1)
        self.run_query(q, 12)

    def test_trim_with_args_weird(self):
        """Trim strings with arguments correctly."""
        q = """from table
            select name
            derive [ trimmed: name | trim " ~something_weird~ " ]
        """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('TRIM(name," ~something_weird~ ") as trimmed') != -1)
        self.run_query(q, 12)

    @pytest.mark.xfail
    def test_trim_with_args_alt(self):
        """Fail when passed incorrectly."""
        q = """from table
            select name
            derive [ trimmed: trim name " ~something_weird~ " ]
        """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('TRIM(name,",") as trimmed') != -1)
        self.run_query(q, 12)

    def test_ltrim(self):
        """Ltrim strings correctly."""
        q = "from table | select name  | derive trimmed: name | ltrim | take 5"
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("LTRIM(name) as trimmed") != -1)
        self.run_query(q, 5)

    def test_ltrim_with_args(self):
        """Ltrim strings with args correctly."""
        q = """from table
            select name
            derive [ trimmed: name | ltrim "," ]
        """
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index('LTRIM(name,",") as trimmed') != -1)
        self.run_query(q, 12)

    def test_rtrim(self):
        """Rtrim strings correctly."""
        q = "from table | select name  | derive trimmed: name | rtrim | take 5"
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("RTRIM(name) as trimmed") != -1)
        self.run_query(q, 5)

    def test_rtrim_with_args(self):
        """Rtrim strings with args correctly."""
        q = """from table
            select name
            derive [ trimmed: name | rtrim "," ]
        """
        res = prql.to_sql(q)
        print(res)
        self.assertTrue(res.index('RTRIM(name,",") as trimmed') != -1)
        self.run_query(q, 12)

    def test_nested_trims(self):
        """Handle multiple trims correctly."""
        q = """from table
        select name
        derive [
            trimmed: name | rtrim ,
            trimmed2: (name | rtrim ",") | ltrim
        ]"""
        res = prql.to_sql(q)
        # print(res)
        self.assertTrue(res.index("RTRIM(name) as trimmed") != -1)
        self.run_query(q, 12)

    def test_replace_function(self):
        """Replace strings correctly."""
        q = """
        from table
        select name
        derive cleaned: name | replace "foo" "bar"

        """
        res = prql.to_sql(q, verbose=True)
        self.assertTrue(res.index('REPLACE(name,"foo","bar") as cleaned') > 0)
        # print(res)
        self.run_query(q, 12)

    def test_substr(self):
        """Find substrings correctly."""
        q = """
        from table | select name | derive [ short: name | substr 0 3 ]"""
        res = prql.to_sql(q, verbose=True)
        # print(res)
        self.assertTrue(res.index("SUBSTR(name,0,3) as short") > 0)
        self.run_query(q, 12)
