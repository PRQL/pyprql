from __future__ import annotations
import polars as pl
import prqlc

from typing import TypeVar, Generic


T_DF = TypeVar("T_DF", pl.DataFrame, pl.LazyFrame)


@pl.api.register_dataframe_namespace("prql")
@pl.api.register_lazyframe_namespace("prql")
class PrqlNamespace(Generic[T_DF]):
    def __init__(self, df: T_DF):
        self._df = df

    def query(self, prql_query: str, *, table_name: str | None = None) -> T_DF:
        prepended_query: str = f"from self \n {prql_query}"
        sql_query: str = prqlc.compile(
            prepended_query,
            options=prqlc.CompileOptions(
                target="sql.any", format=False, signature_comment=False
            ),
        )
        return self._df.sql(sql_query, table_name=table_name)
