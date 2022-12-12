import pandas as pd
import prql_python as prql
import pytest


@pytest.fixture(autouse=True)
def import_accessor():
    import pyprql.pandas_accessor  # noqa


def test_pyql_python():
    """It compiles sql from prql."""
    sql = prql.to_sql("from employees | select [ name, age ]").replace("\n", " ")
    assert sql == "SELECT   name,   age FROM   employees"


def test_df_accessor():
    df = pd.DataFrame({"latitude": [1, 2, 3], "longitude": [1, 2, 3]})
    res = df.prql.query("select [latitude, longitude] | filter latitude > 1")
    assert len(res.index) == 2
    assert res.iloc[0]["latitude"] == 2
    assert res.iloc[1]["latitude"] == 3


def test_df_supports_grouped_aggs():
    rows = {
        "title": ["ceo", "developer", "wizard"],
        "country": ["USA", "USA", "Slovenia"],
        "salary": [120, 100, 130],
    }
    df = pd.DataFrame(rows)
    res = df.prql.query(
        """
        group [country] (
          aggregate [
            avg_sal = average salary,
            ct = count
          ]
        )
        """
    )

    row1 = res.iloc[0]
    row2 = res.iloc[1]

    assert row1["country"] == "USA"
    assert row2["country"] == "Slovenia"

    assert row1["avg_sal"] == 110
    assert row2["avg_sal"] == 130


def test_df_big_prql_query():
    q = """
        filter start_date > @2021-01-01
        derive [
          gross_salary = salary + tax ?? 0,
          gross_cost = gross_salary + benefits_cost,
        ]
        filter gross_cost > 0
        group [title, country] (
          aggregate [
            avg_gross_salary = average gross_salary,
            sum_gross_cost = sum gross_cost,
            cnt = count
          ]
        )
        filter sum_gross_cost > 100
        derive id = f"{title}_{country}"
        sort [sum_gross_cost, -country]
        take 1..20
        """
    rows = {
        "title": ["developer", "developer", "wizard", "horologist"],
        "country": ["USA", "USA", "Slovenia", "Slovenia"],
        "benefits_cost": [10, 20, 50, 0],
        "salary": [120, 100, 130, 0],
        "tax": [1, 1, 2, 0],
        "start_date": [
            pd.Timestamp("2022-01-01"),
            pd.Timestamp("2022-01-02"),
            pd.Timestamp("2022-01-03"),
            pd.Timestamp("2020-01-01"),
        ],
    }
    df = pd.DataFrame(rows)
    res = df.prql.query(q)
    row1 = res.iloc[0]
    row2 = res.iloc[1]

    assert len(res.index) == 2

    assert row1["country"] == "Slovenia"
    assert row1["cnt"] == 1  # the other slovenia was hired in 2020
    assert row1["avg_gross_salary"] == 132
    assert row1["sum_gross_cost"] == 182
    assert row1["id"] == "wizard_Slovenia"

    assert row2["country"] == "USA"
    assert row2["cnt"] == 2
    assert row2["avg_gross_salary"] == 111
    assert row2["sum_gross_cost"] == 252
    assert row2["id"] == "developer_USA"
