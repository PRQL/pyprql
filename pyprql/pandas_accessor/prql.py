"""Pandas Dataframe accessor for PRQL.

Examples
--------
import  pandas as pd
import pyprql.pandas
df = pd.DataFrame({})
results_df = df.prql.query('select [age,name,occupation] | filter age > 21')

"""

import duckdb
import pandas as pd
import prql_python as prql


@pd.api.extensions.register_dataframe_accessor("prql")
class PrqlAccessor:
    def __init__(self, pandas_obj: object) -> None:
        self._obj = pandas_obj

    def query(self, prql_query: str) -> pd.DataFrame:
        prepended_query = f"from df \n {prql_query}"
        sql_query = prql.to_sql(prepended_query)
        return duckdb.query_df(
            self._obj,
            virtual_table_name="df",
            sql_query=sql_query,
        ).fetch_df()
