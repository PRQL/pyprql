import prql_python as prql


def test_pyql_python():
    sql = prql.to_sql("from employees | select [ name, age ]")
    print(sql)
