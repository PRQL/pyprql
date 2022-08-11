# -*- coding: utf-8 -*-
"""Pandas Dataframe accessor for PRQL.

Examples
--------
import  pandas as pd
import pyprql.pandas
df = pd.DataFrame({})
results_df = df.prql.query('from df | select [age,name,occupation] | filter age > 21')

"""

import pandas as pd
import prql_python as prql

import duckdb


@pd.api.extensions.register_dataframe_accessor("prql")
class PrqlAccessor:

    def __init__(self, pandas_obj : object) -> None:
        self._obj = pandas_obj

    def query(self, prql_query : str) -> pd.DataFrame:
        return duckdb.query(prql.to_sql(prql_query)).to_df()
