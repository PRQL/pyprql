import prql_python as prql


class PyqlPythonTest(object):
    def test_pyql_python(self):
        sql = prql.to_sql("from employees | select [ name, age ]")
        print(sql)
