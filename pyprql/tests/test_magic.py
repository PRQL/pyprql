"""
These tests are heavily borrowed from
https://github.com/ploomber/jupysql/blob/0.5.1/src/tests/test_magic.py

Many are xfailed because we don't yet support them. Others are lightly adapted for PRQL,
and there are some TODOs around a fuller transition.

Thanks to @ploomber for providing the base for these tests as well as the extension.
"""


import os.path
import re
import tempfile
from textwrap import dedent

import polars as pl
import pytest
from sqlalchemy import create_engine

from pyprql.tests import run_sql

from . import run_prql


def test_memory_db(ip, regtest):
    print(run_prql(ip, "from test"), file=regtest)


def test_html(ip):
    result = run_prql(ip, "from test")
    assert "<td>foo</td>" in result._repr_html_().lower()


def test_line_magic(ip):
    result = ip.run_line_magic("prql", "from      test   |     select [name]")
    assert "foo" in str(result)


@pytest.mark.skip(reason="We only support pandas")
def test_print(ip):
    result = run_prql(ip, "from test")
    assert re.search(r"1\s+\|\s+foo", str(result))


@pytest.mark.skip(reason="We only support pandas")
def test_plain_style(ip):
    ip.run_line_magic("config", "SqlMagic.style = 'PLAIN_COLUMNS'")
    result = run_prql(ip, "from test")
    assert re.search(r"1\s+\|\s+foo", str(result))


@pytest.mark.skip
def test_multi_sql(ip):
    result = ip.run_cell_magic(
        "prql",
        "",
        """
        sqlite://
        from author
        """,
    )
    assert "Shakespeare" in str(result) and "Brecht" in str(result)


def test_result_var(ip, capsys):
    ip.run_line_magic("config", "SqlMagic.autopandas = False")
    ip.run_cell_magic(
        "prql",
        "sqlite:// x <<",
        """
        from author
        select last_name
        """,
    )
    result = ip.user_global_ns["x"]
    out, _ = capsys.readouterr()

    assert "Shakespeare" in str(result) and "Brecht" in str(result)
    assert "Returning data to local variable" not in out


@pytest.mark.xfail(reason="Not supported in PRQL")
def test_result_var_multiline_shovel(ip):
    ip.run_cell_magic(
        "prql",
        "",
        """
        x << from author
        select last_name
        """,
    )
    result = ip.user_global_ns["x"]
    assert "Shakespeare" in str(result) and "Brecht" in str(result)


@pytest.mark.skip(reason="We only support pandas")
def test_access_results_by_keys(ip):
    assert run_prql(ip, "from author")["author"] == (
        "William",
        "Shakespeare",
        1616,
    )


def test_duplicate_column_names_accepted(ip):
    ip.run_line_magic("config", "SqlMagic.autopandas = False")
    result = ip.run_cell_magic(
        "prql",
        "sqlite://",
        """
        from author | select [last_name, last_name]
        """,
    )
    assert ("Brecht", "Brecht") in result


def test_persist(ip):
    ip.run_line_magic("config", "SqlMagic.autopandas = False")
    run_prql(ip, "")
    ip.run_cell("results = %prql from test")
    ip.run_cell("results_dframe = results.DataFrame()")
    ip.run_cell("%sql --persist sqlite:// results_dframe")
    persisted = run_prql(ip, "from results_dframe")
    assert persisted == [(0, 1, "foo"), (1, 2, "bar")]


def test_persist_no_index(ip):
    ip.run_line_magic("config", "SqlMagic.autopandas = False")
    run_prql(ip, "")
    ip.run_cell("results = %prql from test")
    ip.run_cell("results_no_index = results.DataFrame()")
    ip.run_cell("%prql --persist sqlite:// results_no_index --no-index")
    persisted = run_prql(ip, "from results_no_index")
    assert persisted == [(1, "foo"), (2, "bar")]


def test_append(ip):
    ip.run_line_magic("config", "SqlMagic.autopandas = False")
    run_prql(ip, "")
    ip.run_cell("results = %prql from test")
    ip.run_cell("results_dframe_append = results.DataFrame()")
    ip.run_cell("%prql --persist sqlite:// results_dframe_append")
    persisted = run_prql(ip, "from results_dframe_append")
    ip.run_cell("%prql --append sqlite:// results_dframe_append")
    appended = run_prql(ip, "from results_dframe_append")
    assert appended[0][0] == persisted[0][0] * 2


def test_persist_nonexistent_raises(ip):
    run_prql(ip, "")
    result = ip.run_cell("%prql --persist sqlite:// no_such_dataframe")
    assert result.error_in_exec


def test_persist_non_frame_raises(ip):
    ip.run_cell("not_a_dataframe = 22")
    run_prql(ip, "")
    result = ip.run_cell("%prql --persist sqlite:// not_a_dataframe")
    assert result.error_in_exec


def test_persist_bare(ip):
    result = ip.run_cell("%prql --persist sqlite://")
    assert result.error_in_exec


@pytest.mark.xfail(reason="Need to resolve line vs cell magic")
def test_persist_frame_at_its_creation(ip):
    ip.run_cell("results = %sql from author")
    ip.run_cell("%sql --persist sqlite:// results.DataFrame()")
    persisted = run_prql(ip, "from results")
    assert "Shakespeare" in str(persisted)


def test_connection_args_enforce_json(ip):
    result = ip.run_cell('%sql --connection_arguments {"badlyformed":true')
    assert result.error_in_exec


def test_connection_args_in_connection(ip):
    ip.run_cell('%sql --connection_arguments {"timeout":10} sqlite:///:memory:')
    result = ip.run_cell("%sql --connections")
    assert "timeout" in result.result["sqlite:///:memory:"].connect_args


def test_connection_args_single_quotes(ip):
    ip.run_cell("%sql --connection_arguments '{\"timeout\": 10}' sqlite:///:memory:")
    result = ip.run_cell("%sql --connections")
    assert "timeout" in result.result["sqlite:///:memory:"].connect_args


def test_connection_args_double_quotes(ip):
    ip.run_cell('%sql --connection_arguments "{\\"timeout\\": 10}" sqlite:///:memory:')
    result = ip.run_cell("%sql --connections")
    assert "timeout" in result.result["sqlite:///:memory:"].connect_args


# TODO: support
# @with_setup(_setup_author, _teardown_author)
# def test_persist_with_connection_info():
#     ip.run_cell("results = %sql from author")
#     ip.run_line_magic('sql', 'sqlite:// PERSIST results.DataFrame()')
#     persisted = ip.run_line_magic('sql', 'SELECT * FROM results')
#     assert 'Shakespeare' in str(persisted)


@pytest.mark.xfail(reason="Need to implement sample data in PRQL")
def test_displaylimit(ip, regtest):
    ip.run_line_magic("config", "SqlMagic.autolimit = None")
    ip.run_line_magic("config", "SqlMagic.displaylimit = None")
    result = run_prql(
        ip,
        "SELECT * FROM (VALUES ('apple'), ('banana'), ('cherry')) "
        "AS Result ORDER BY 1;",
    )
    regtest.write(result._repr_html_(), file=regtest)

    assert "apple" in result._repr_html_()
    assert "banana" in result._repr_html_()
    assert "cherry" in result._repr_html_()

    ip.run_line_magic("config", "SqlMagic.displaylimit = 1")
    result = run_prql(
        ip,
        "SELECT * FROM (VALUES ('apple'), ('banana'), ('cherry')) "
        "AS Result ORDER BY 1;",
    )
    assert "apple" in result._repr_html_()
    assert "cherry" not in result._repr_html_()


@pytest.mark.xfail(reason="Not supported in PRQL")
def test_column_local_vars(ip):
    ip.run_line_magic("config", "SqlMagic.column_local_vars = True")
    result = run_prql(ip, "from author")
    assert result is None
    assert "William" in ip.user_global_ns["first_name"]
    assert "Shakespeare" in ip.user_global_ns["last_name"]
    assert len(ip.user_global_ns["first_name"]) == 2
    ip.run_line_magic("config", "SqlMagic.column_local_vars = False")


@pytest.mark.skip(reason="Not supported in PRQL")
def test_userns_not_changed(ip):
    ip.run_cell(
        dedent(
            """
    def function():
        local_var = 'local_val'
        %sql sqlite:// INSERT INTO test VALUES (2, 'bar');
    function()"""
        )
    )
    assert "local_var" not in ip.user_ns


@pytest.mark.xfail(reason="Not supported in PRQL")
def test_bind_vars(ip):
    ip.user_global_ns["x"] = 22
    result = run_prql(ip, "SELECT :x")
    assert result[0][0] == 22


def test_autopandas(ip):
    dframe = run_prql(ip, "from test")
    assert not dframe.empty
    assert dframe.ndim == 2
    assert dframe.name[0] == "foo"


def test_autopolars(ip):
    ip.run_line_magic("config", "PrqlMagic.autopolars = True")
    dframe = run_prql(ip, "from test")

    assert type(dframe) == pl.DataFrame
    assert not dframe.is_empty()
    assert len(dframe.shape) == 2
    assert dframe["name"][0] == "foo"


def test_target_dialect(ip):
    ip.run_line_magic("config", 'PrqlMagic.target = "sql.sqlite"')
    dframe = run_prql(
        ip, 'from author | select foo = f"{first_name}-{last_name}" | take 1'
    )
    assert dframe.foo[0] == "William-Shakespeare"


def test_without_target(ip, capsys):
    run_prql(ip, 'from author | select foo = f"{first_name}-{last_name}" | take 1')
    captured = capsys.readouterr()
    assert captured.out.startswith(
        "(sqlite3.OperationalError) no such function: CONCAT"
    )


def test_dryrun(ip, capsys):
    ip.run_line_magic("config", "PrqlMagic.dryrun = True")
    result = run_prql(ip, 'from a | select b = f"{c}-{d}"')
    captured = capsys.readouterr()
    assert captured.out.startswith("SELECT\n  CONCAT")
    assert result is None


def test_csv(ip):
    ip.run_line_magic("config", "SqlMagic.autopandas = False")  # uh-oh
    result = run_prql(ip, "from test")
    result = result.csv()
    for row in result.splitlines():
        assert row.count(",") == 1
    assert len(result.splitlines()) == 3


def test_csv_to_file(ip):
    ip.run_line_magic("config", "SqlMagic.autopandas = False")  # uh-oh
    result = run_prql(ip, "from test")
    with tempfile.TemporaryDirectory() as tempdir:
        fname = os.path.join(tempdir, "test.csv")
        output = result.csv(fname)
        assert os.path.exists(output.file_path)
        with open(output.file_path) as csvfile:
            content = csvfile.read()
            for row in content.splitlines():
                assert row.count(",") == 1
            assert len(content.splitlines()) == 3


def test_sql_from_file(ip):
    ip.run_line_magic("config", "PrqlMagic.autopandas = False")
    with tempfile.TemporaryDirectory() as tempdir:
        fname = os.path.join(tempdir, "test.sql")
        with open(fname, "w") as tempf:
            tempf.write("from test")
        result = ip.run_cell("%prql --file " + fname)
        assert result.result == [(1, "foo"), (2, "bar")]
        result = ip.run_cell("%prql -f " + fname)
        assert result.result == [(1, "foo"), (2, "bar")]


def test_sql_from_nonexistent_file(ip):
    ip.run_line_magic("config", "PrqlMagic.autopandas = False")
    with tempfile.TemporaryDirectory() as tempdir:
        fname = os.path.join(tempdir, "nonexistent.sql")
        result = ip.run_cell("%prql --file " + fname)
        assert isinstance(result.error_in_exec, FileNotFoundError)


@pytest.mark.skip("We only support pandas")
def test_dict(ip):
    result = run_prql(ip, "from author")
    result = result.dict()
    assert isinstance(result, dict)
    assert "first_name" in result
    assert "last_name" in result
    assert "year_of_death" in result
    assert len(result["last_name"]) == 2


@pytest.mark.skip("We only support pandas")
def test_dicts(ip):
    result = run_prql(ip, "from author")
    for row in result.dicts():
        assert isinstance(row, dict)
        assert "first_name" in row
        assert "last_name" in row
        assert "year_of_death" in row


@pytest.mark.xfail(reason="Not supported in PRQL")
def test_bracket_var_substitution(ip):
    ip.user_global_ns["col"] = "first_name"
    assert run_prql(ip, "from author | filter WHERE {col} = 'William' ")[0] == (
        "William",
        "Shakespeare",
        1616,
    )

    ip.user_global_ns["col"] = "last_name"
    result = run_prql(ip, "from author | filter WHERE {col} = 'William' ")
    assert not result


# the next two tests had the same name, so I added a _2 to the second one
@pytest.mark.xfail(reason="Not supported in PRQL")
def test_multiline_bracket_var_substitution(ip):
    ip.user_global_ns["col"] = "first_name"
    assert run_prql(ip, "SELECT * FROM author\n" " WHERE {col} = 'William' ")[0] == (
        "William",
        "Shakespeare",
        1616,
    )

    ip.user_global_ns["col"] = "last_name"
    result = run_prql(ip, "SELECT * FROM author" " WHERE {col} = 'William' ")
    assert not result


@pytest.mark.xfail(reason="Not supported in PRQL")
def test_multiline_bracket_var_substitution_2(ip):
    ip.user_global_ns["col"] = "first_name"
    result = ip.run_cell_magic(
        "prql",
        "",
        """
        sqlite:// SELECT * FROM author
        WHERE {col} = 'William'
        """,
    )
    assert ("William", "Shakespeare", 1616) in result

    ip.user_global_ns["col"] = "last_name"
    result = ip.run_cell_magic(
        "prql",
        "",
        """
        sqlite:// SELECT * FROM author
        WHERE {col} = 'William'
        """,
    )
    assert not result


def test_json_in_select(ip):
    # Variable expansion does not work within json, but
    # at least the two usages of curly braces do not collide
    ip.user_global_ns["person"] = "prince"
    result = ip.run_cell_magic(
        "sql",
        "",
        """
        sqlite://
        SELECT
          '{"greeting": "Farewell sweet {person}"}'
        AS json
        """,
    )

    assert result == [('{"greeting": "Farewell sweet {person}"}',)]


def test_close_connection(ip):
    # TODO: change this to testing run_prql
    connections = run_sql(ip, "%sql -l")
    connection_name = list(connections)[0]
    run_sql(ip, f"%sql -x {connection_name}")
    connections_afterward = run_sql(ip, "%sql -l")
    assert connection_name not in connections_afterward


def test_pass_existing_engine(ip, tmp_empty, regtest):
    ip.user_global_ns["my_engine"] = create_engine("sqlite:///my.db")
    ip.run_line_magic("sql", "  my_engine ")

    run_sql(
        ip,
        [
            "CREATE TABLE some_data (n INT, name TEXT)",
            "INSERT INTO some_data VALUES (10, 'foo')",
            "INSERT INTO some_data VALUES (20, 'bar')",
        ],
    )

    result = ip.run_line_magic("prql", "from some_data")

    print(result, file=regtest)


# theres some weird shared state with this one, moving it to the end
def test_autolimit(ip):
    ip.run_line_magic("config", "SqlMagic.autolimit = 0")
    result = run_prql(ip, "from test")
    assert len(result) == 2
    ip.run_line_magic("config", "SqlMagic.autolimit = 1")
    result = run_prql(ip, "from test")
    assert len(result) == 1
    assert len(result) == 1
    assert len(result) == 1
