import sqlite3

import prql
from prql import parse, read_file, script_path, ast_to_sql

if __name__ == '__main__':
    base_path = '/../tests/factbook_examples'
    db_path = script_path + f'/{base_path}/factbook.db'
    # print(f'Using database: {db_path}')
    # con = sqlite3.connect(db_path)
    # cur = con.cursor()

    # text = read_file(file_name)
    text = '''
    from facts
        join cities [id=facts_id]
        derive [
            city: "cities.name",
            country: "facts.name"
        ]
        aggregate by:[code] [
            country_pop: cities.population | sum ,
            city_pop: sum cities.population 
        ]
        sort "city_pop desc"
        take 5        
        
    '''

    if text:
        sql = prql.to_sql(text)
        print(f'PRQL->SQL: {sql}\n' + '~' * 80 + '\n')
