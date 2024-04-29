import polars as pl
import prqlc


@pl.api.register_dataframe_namespace("prql")
@pl.api.register_lazyframe_namespace("prql")
class PrqlNamespace:
    def __init__(self, df: pl.DataFrame | pl.LazyFrame):
        self._df = df

    def query(
        self, prql_query: str, *, table_name: str | None = None
    ) -> pl.DataFrame | pl.LazyFrame:
        prepended_query: str = f"from self \n {prql_query}"
        sql_query: str = prqlc.compile(
            prepended_query,
            options=prqlc.CompileOptions(
                target="sql.any", format=False, signature_comment=False
            ),
        )
        return self._df.sql(sql_query, table_name=table_name)
