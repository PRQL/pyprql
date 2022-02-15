import sqlite3

from prql import parse, read_file, script_path, ast_to_sql

if __name__ == '__main__':
    base_path = '/../tests/factbook_examples'
    db_path = script_path + f'/{base_path}/factbook.db'
    print(f'Using database: {db_path}')
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    file_names = ['/../resources/stdlib.prql']
    for file_name in file_names:
        text = read_file(file_name)

        print('\n' + '-' * 80 + f'\nParsing {file_name}\n' + '-' * 80 + '\n' + text + '\n' + '-' * 80)
        if text:
            tree = parse(text)

            # try:
            sql = ast_to_sql(tree._from, [tree])
            print(f'PRQL->SQL: {sql}\n' + '~' * 80 + '\n')

            rows = cur.execute(sql)
            columns = [d[0] for d in rows.description]
            rows = rows.fetchall()

            for row in rows:
                print(row)

            # except Exception as e:
            #     print(f'\n\nError: {e}\n\n')
            #     #raise e
