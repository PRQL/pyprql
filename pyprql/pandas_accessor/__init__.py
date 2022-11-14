"""Init file for pyprql.pandas.

Examples
--------
import  pandas as pd
import pyprql.pandas
df = pd.DataFrame({})
results_df = df.prql.query('select [age,name,occupation] | filter age > 21')

"""
import pyprql.pandas_accessor.prql  # noqa: F401
