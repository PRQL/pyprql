import polars as pl
import pytest


@pytest.fixture(autouse=True)
def import_accessor():
    import pyprql.polars_namespace  # noqa


def test_polars_df_namespace():
    df = pl.DataFrame({"latitude": [1, 2, 3], "longitude": [1, 2, 3]})
    res = df.prql.query(
        "select {latitude, longitude} | filter latitude > 1 | sort latitude"
    )
    assert res.to_dict(as_series=False) == {
        "latitude": [2, 3],
        "longitude": [2, 3],
    }


def test_polars_lf_namespace():
    df = pl.LazyFrame({"latitude": [1, 2, 3], "longitude": [1, 2, 3]})
    res = df.prql.query(
        "select {latitude, longitude} | filter latitude > 1 | sort latitude"
    ).collect()
    assert res.to_dict(as_series=False) == {
        "latitude": [2, 3],
        "longitude": [2, 3],
    }
