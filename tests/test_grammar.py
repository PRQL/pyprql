# -*- coding: utf-8 -*-
"""Tests for grammars."""
import sqlite3
import unittest
from pathlib import Path

import pytest
from lark.exceptions import UnexpectedToken

from pyprql.lang import prql


class TestSqlGenerator(unittest.TestCase):
    """An unittest.TestCase."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up tests."""
        # Use Path for robust construction, but sqlite3 py3.6 requires str
        db_path = str(Path("tests", "../resources/chinook.db"))
        cls.con = sqlite3.connect(db_path)  # type:ignore[attr-defined]
        cls.cur = cls.con.cursor()  # type:ignore[attr-defined]

    def run_query(self, text, expected=None, verbose=False):
        """Run a query."""
        # print(text.replace('\n\n', '\n'))
        # print('-' * 40)
        sql = prql.to_sql(text, verbose)
        # print(sql)

        rows = self.cur.execute(sql)
        _ = [d[0] for d in rows.description]
        # print(f'Columns: {columns}')
        rows = rows.fetchall()
        if expected is not None:
            assert len(rows) == expected

        return sql

    def test_expressions_in_filter(self):
        """Evaluate expressions in filters."""
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
        """Evaluate expressions with parentheses in filters."""
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
        """Evaluate expressions with parentheses in derives."""
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
        """Evaluate expressions in derives."""
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
        """Evaluate heavily nested expressions."""
        q = """
        from tracks
        filter t.Milliseconds * (t.TrackId * (32/(47/72)+(1/8))) > 5 * 60.01 + 3.1
        """
        sql = prql.to_sql(q)
        assert sql.index("t.Milliseconds*(t.TrackId*(32/(47/72)+(1/8)))") > 0

    def test_aggregates_grammar(self):
        """Parse aggregate statements correctly."""
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
        """Parse nested aggregate statements correctly."""
        q = """
        from tracks
        aggregate  by:t.Composer [
            row_count: (t.TrackId | count) | max
        ]
        """
        sql = prql.to_sql(q)
        assert sql.index("SELECT MAX(COUNT(t.TrackId))") == 0

    def test_to_grammar(self):
        """Parse to statements correctly."""
        q = """
        from t:tracks
        select t.Composer
        to csv test.csv
        """
        sql = prql.to_sql(q)
        assert sql.index("TO csv test.csv") == 45

    def test_to_grammar_not_at_end(self):
        """Error when to is not the last statment."""
        q = """
        from t:tracks
        to csv test.csv
        select t.Composer
        """
        with pytest.raises(UnexpectedToken):
            _ = prql.to_sql(q)

    def test_to_grammar_complex(self):
        """Parse to statements with complex file names correctly."""
        filenames = ["~/a/more/complex/../test.csv", r"C:\a\more\complex\test.csv"]
        for file in filenames:
            with self.subTest():
                q = f"""
                from t:tracks
                select t.Composer
                to csv {file}
                """
                sql = prql.to_sql(q)
                assert sql.index(f"TO csv {file}") == 45
