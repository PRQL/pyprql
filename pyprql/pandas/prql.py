import duckdb
import pandas as pd
import prql_python as prql


@pd.api.extensions.register_dataframe_accessor("prql")
class PrqlAccessor:
    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        # verify there is a column latitude and a column longitude
        return True

    def query(self, q):  # -> pd.DataFrame:
        return duckdb.query(prql.to_sql(q)).to_df()
