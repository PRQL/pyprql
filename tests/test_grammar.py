# -*- coding: utf-8 -*-
import sqlite3
import unittest
from pathlib import Path

import pytest
from lark.exceptions import UnexpectedToken

from pyprql.lang import prql


class TestSqlGenerator(unittest.TestCase):
    def setUpClass() -> None:
        # Use Path for robust construction, but sqlite3 py3.6 requires str
        db_path = str(Path("tests", "../resources/chinook.db"))
        TestSqlGenerator.con = sqlite3.connect(db_path)
        TestSqlGenerator.cur = TestSqlGenerator.con.cursor()

    def run_query(self, text, expected=None, verbose=False):
        # print(text.replace('\n\n', '\n'))
        # print('-' * 40)
        sql = prql.to_sql(text, verbose)
        # print(sql)

        rows = TestSqlGenerator.cur.execute(sql)
        columns = [d[0] for d in rows.description]
        # print(f'Columns: {columns}')
        rows = rows.fetchall()
        if expected is not None:
            assert len(rows) == expected

        return sql

    def test_expressions_in_filter(self):
        # Songs greater than 5 minutes

        q = """
        from t:tracks
        select t.Composer
        filter t.Milliseconds * 1000 > 5 * 60
        take 23
        """
        res = prql.to_sql(q)
        assert res.index("t.Milliseconds*1000>5*60") > 0
        self.run_query(q, 23)

    def test_expressions_in_filter_w_parens(self):
        # Songs greater than 5 minutes

        q = """
        from t:tracks
        select t.Composer
        filter (t.Milliseconds * 1000) > 5 * 60
        take 23
        """
        res = prql.to_sql(q)
        print(res)
        assert res.index("(t.Milliseconds*1000)>5*60") > 0
        self.run_query(q, 23)

    def test_expression_in_derive(self):
        q = """
        from t:tracks
        join a:albums [ AlbumId ]
        join mt:media_types [ MediaTypeId ]
        join g:genres [ GenreId ]
        derive [
            track: t.Name,
            minutes: (t.Milliseconds / 1000.0) / 60.0
        ]
        select t.Composer
        """
        sql = self.run_query(q)
        assert sql.index("(t.Milliseconds/1000.0)/60.0") > 0

    def test_expression_in_derive_without_parens(self):
        q = """
        from t:tracks
        join a:albums [ AlbumId ]
        join mt:media_types [ MediaTypeId ]
        join g:genres [ GenreId ]
        derive [
            track: t.Name,
            minutes: t.Milliseconds / 1000.0 / 60.0
        ]
        select t.Composer
        """
        sql = self.run_query(q)
        assert sql.index("t.Milliseconds/1000.0/60.0") > 0

    def test_hypothetical_with_lots_of_sub_expressions(self):
        q = """
        from tracks
        filter t.Milliseconds * (t.TrackId * (32/(47/72)+(1/8))) > 5 * 60.01 + 3.1
        """
        sql = prql.to_sql(q)
        print(sql)
        assert sql.index("t.Milliseconds*(t.TrackId*(32/(47/72)+(1/8)))") > 0

    def test_aggregates_grammar(self):
        q = """
        from tracks
        aggregate  by:t.Composer [
            row_count: t.TrackId | count
        ]
        """
        sql = prql.to_sql(q)
        assert sql.index("COUNT(t.TrackId) as row_count") == 7
        assert sql.index("GROUP BY t.Composer") == 70

    def test_aggregates_grammar_nested(self):
        q = """
        from tracks
        aggregate  by:t.Composer [
            row_count: (t.TrackId | count) | max
        ]
        """
        sql = prql.to_sql(q)
        assert sql.index("SELECT MAX(COUNT(t.TrackId))") == 0

    def test_to_grammar(self):
        q = """
        from t:tracks
        select t.Composer
        to csv test.csv
        """
        sql = prql.to_sql(q)
        assert sql.index("TO csv test.csv") == 45

    def test_to_grammar_not_at_end(self):
        q = """
        from t:tracks
        to csv test.csv
        select t.Composer
        """
        with pytest.raises(UnexpectedToken):
            sql = prql.to_sql(q)

    @pytest.mark.xfail
    def test_to_grammar_complex_file(self):
        q = """
        from t:tracks
        select t.Composer
        to csv ~/a/more/complex/test.csv
        """
        sql = prql.to_sql(q)
        assert sql.index("TO csv ~/a/more/complex/test.csv") == 45
