import sqlite3

from prql import parse,  read_file, script_path, SQLGenerator

if __name__ == '__main__':
    base_path = '/factbook_examples'
    file_names = [
        f'/{base_path}/q1.prql',
        f'/{base_path}/q2.prql',
        f'/{base_path}/q3.prql',
        f'/{base_path}/q3b.prql',
        f'/{base_path}/sql/simple_join.prql',
        f'/{base_path}/sql/better_join.prql'
    ]
    # f'{base_path}test_query2.prql',f'{base_path}test_query1.prql',

    db_path = script_path + f'{base_path}/factbook.db'
    print(f'Opening database {db_path}')
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    for file_name in file_names:
        text = read_file(file_name)
        print('*' * 80)
        print(f'Parsing {file_name}\n' + '*' * 80)
        print(text)
        print('-' * 80)
        if text:
            tree = parse(text)
            sql_generator = SQLGenerator(tree)

            # pretty_print(tree)
            try:

                sql = sql_generator.generate()
                print(f'Executing: \n\n{sql}\n')
                #sql = tree_to_sql(tree)
                rows = cur.execute(sql)
                columns = [d[0] for d in rows.description]
                print(columns)
                for row in rows:
                    print(row)

            except Exception as e:
                print(f'\n\nError: {e}\n\n')
