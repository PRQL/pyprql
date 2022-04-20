# -*- coding: utf-8 -*-
"""Tests for grammars."""
import sqlite3
import unittest
from pathlib import Path

import pytest
from lark.exceptions import UnexpectedToken

from pyprql.lang import prql


class TestDBT(unittest.TestCase):
    """An unittest.TestCase."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up tests."""
        # Use Path for robust construction, but sqlite3 py3.6 requires str
        db_path = str(Path("tests", "../resources/chinook.db"))
        cls.con = sqlite3.connect(db_path)  # type:ignore[attr-defined]
        cls.cur = cls.con.cursor()  # type:ignore[attr-defined]

    def test_ref_relation(self):
        """Pass macro without changing it"""
        q = """
        from {{ ref('my_model') }}
        """
        sql = prql.to_sql(q)
        assert sql.index("FROM {{ ref('my_model') }} refmy_model") != -1

    def test_source_relation(self):
        """Pass macro without changing it"""
        q = """
        from {{ source('my_source', 'my_table') }}
        """
        sql = prql.to_sql(q)
        assert (
            sql.index(
                "FROM {{ source('my_source', 'my_table') }} sourcemy_sourcemy_table"
            )
            != -1
        )

    def test_macro_alias_relation(self):
        """Pass macro with alias correctly"""
        q = """
        from {{ ref('my_model') }} alias
        """
        sql = prql.to_sql(q)
        assert sql.index("FROM `{{ ref('my_model') }}` alias") != -1
