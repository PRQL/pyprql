import os
import urllib.request
from pathlib import Path

import pytest
from IPython.core.interactiveshell import InteractiveShell
from sql.magic import RenderMagic, SqlMagic

from pyprql.magic import PrqlMagic
from pyprql.tests import run_sql

PATH_TO_TESTS = Path(__file__).absolute().parent
PATH_TO_TMP_ASSETS = PATH_TO_TESTS / "tmp"
PATH_TO_TMP_ASSETS.mkdir(exist_ok=True)


def path_to_tests():
    return PATH_TO_TESTS


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
def ip():
    """Provides an IPython session in which tables have been created"""
    ip_session = InteractiveShell()
    ip_session.register_magics(SqlMagic)
    ip_session.register_magics(PrqlMagic)
    ip_session.register_magics(RenderMagic)

    # run_prql creates an inmemory sqlitedatabase
    run_sql(
        ip_session,
        [
            "CREATE TABLE test (n INT, name TEXT)",
            "INSERT INTO test VALUES (1, 'foo')",
            "INSERT INTO test VALUES (2, 'bar')",
            "CREATE TABLE author (first_name, last_name, year_of_death)",
            "INSERT INTO author VALUES ('William', 'Shakespeare', 1616)",
            "INSERT INTO author VALUES ('Bertold', 'Brecht', 1956)",
        ],
    )
    yield ip_session
    run_sql(ip_session, "DROP TABLE test")
    run_sql(ip_session, "DROP TABLE author")


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
    os.chdir(old)
    os.chdir(old)
