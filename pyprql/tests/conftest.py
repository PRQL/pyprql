import os
import urllib.request
from pathlib import Path

import pytest
from sql import connection
from sql import _current
from sql._testing import TestingShell
from sql.connection import ConnectionManager
from sql.magic import RenderMagic, SqlMagic
from sql.magic_cmd import SqlCmdMagic
from sql.magic_plot import SqlPlotMagic
from traitlets.config import Config

from pyprql.magic import PrqlMagic

PATH_TO_TESTS = Path(__file__).absolute().parent
PATH_TO_TMP_ASSETS = PATH_TO_TESTS / "tmp"
PATH_TO_TMP_ASSETS.mkdir(exist_ok=True)


def path_to_tests():
    return PATH_TO_TESTS


@pytest.fixture(scope="function", autouse=True)
def isolate_connections(monkeypatch):
    """
    Fixture to ensure connections are isolated between tests, preventing tests
    from accidentally closing connections created by other tests.
    """
    connections = {}
    monkeypatch.setattr(connection.ConnectionManager, "connections", connections)
    monkeypatch.setattr(connection.ConnectionManager, "current", None)
    yield
    connection.ConnectionManager.close_all()


@pytest.fixture
def chinook_db():
    path = PATH_TO_TMP_ASSETS / "my.db"
    if not path.is_file():
        url = (
            "https://raw.githubusercontent.com"
            "/lerocha/chinook-database/master/"
            "ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
        )
        urllib.request.urlretrieve(url, path)

    return str(path)


@pytest.fixture
def ip_empty():
    c = Config()
    # By default, InteractiveShell will record command's history in a SQLite database
    # which leads to "too many open files" error when running tests; this setting
    # disables the history recording.
    # https://ipython.readthedocs.io/en/stable/config/options/terminal.html#configtrait-HistoryAccessor.enabled
    c.HistoryAccessor.enabled = False
    ip_session = TestingShell(config=c)

    sql_magic = SqlMagic(ip_session)
    _current._set_sql_magic(sql_magic)

    ip_session.register_magics(sql_magic)
    ip_session.register_magics(RenderMagic)
    ip_session.register_magics(SqlPlotMagic)
    ip_session.register_magics(SqlCmdMagic)
    ip_session.register_magics(PrqlMagic)
    ip_session.register_magics(RenderMagic)

    # there is some weird bug in ipython that causes this function to hang the pytest
    # process when all tests have been executed (an internal call to gc.collect()
    # hangs). This is a workaround.
    ip_session.displayhook.flush = lambda: None

    yield ip_session
    ConnectionManager.close_all()


def insert_sample_data(ip):
    ip.run_cell(
        """%%sql
CREATE TABLE test (n INT, name TEXT);
INSERT INTO test VALUES (1, 'foo');
INSERT INTO test VALUES (2, 'bar');
CREATE TABLE [table with spaces] (first INT, second TEXT);
CREATE TABLE author (first_name, last_name, year_of_death);
INSERT INTO author VALUES ('William', 'Shakespeare', 1616);
INSERT INTO author VALUES ('Bertold', 'Brecht', 1956);
CREATE TABLE empty_table (column INT, another INT);
CREATE TABLE website (person, link, birthyear INT);
INSERT INTO website VALUES ('Bertold Brecht',
    'https://en.wikipedia.org/wiki/Bertolt_Brecht', 1954 );
INSERT INTO website VALUES ('William Shakespeare',
    'https://en.wikipedia.org/wiki/William_Shakespeare', 1564);
INSERT INTO website VALUES ('Steve Steve', 'google_link', 2023);
CREATE TABLE number_table (x INT, y INT);
INSERT INTO number_table VALUES (4, (-2));
INSERT INTO number_table VALUES ((-5), 0);
INSERT INTO number_table VALUES (2, 4);
INSERT INTO number_table VALUES (0, 2);
INSERT INTO number_table VALUES ((-5), (-1));
INSERT INTO number_table VALUES ((-2), (-3));
INSERT INTO number_table VALUES ((-2), (-3));
INSERT INTO number_table VALUES ((-4), 2);
INSERT INTO number_table VALUES (2, (-5));
INSERT INTO number_table VALUES (4, 3);
"""
    )


@pytest.fixture
def ip(ip_empty):
    """Provides an IPython session in which tables have been created"""
    ip_empty.run_cell("%sql sqlite://")
    insert_sample_data(ip_empty)

    yield ip_empty

    ConnectionManager.close_all()


@pytest.fixture
def ip_dbapi(ip_empty):
    ip_empty.run_cell("import sqlite3; conn = sqlite3.connect(':memory:');")
    ip_empty.run_cell("%sql conn")
    insert_sample_data(ip_empty)

    yield ip_empty

    ConnectionManager.close_all()


# @pytest.fixture
# def ip():
#     """Provides an IPython session in which tables have been created"""
#     ip_session = InteractiveShell()
#     ip_session.register_magics(SqlMagic)

#     # run_prql creates an inmemory sqlitedatabase
#     run_sql(
#         ip_session,
#         [
#             "CREATE TABLE test (n INT, name TEXT)",
#             "INSERT INTO test VALUES (1, 'foo')",
#             "INSERT INTO test VALUES (2, 'bar')",
#             "CREATE TABLE author (first_name, last_name, year_of_death)",
#             "INSERT INTO author VALUES ('William', 'Shakespeare', 1616)",
#             "INSERT INTO author VALUES ('Bertold', 'Brecht', 1956)",
#         ],
#     )
#     yield ip_session
#     run_sql(ip_session, "DROP TABLE test")
#     run_sql(ip_session, "DROP TABLE author")


@pytest.fixture
def tmp_empty(tmp_path):
    """
    Create temporary path using pytest native fixture,
    them move it, yield, and restore the original path
    """

    old = os.getcwd()
    os.chdir(str(tmp_path))
    yield str(Path(tmp_path).resolve())
    os.chdir(old)
