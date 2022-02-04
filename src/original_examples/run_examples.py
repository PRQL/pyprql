from prql import parse, pretty_print, tree_to_sql, read_file,script_path

if __name__ == '__main__':



    file_name = '/original_examples/cte1.prql'
    text = read_file(file_name)
    print('*' * 80)
    print(f'Parsing {file_name}\n' + '*' * 80 )
    print(text)
    print('-' * 80)
    tree = parse(text)
    print('AST: pretty_print(tree)')
    print('-' * 80)

    pretty_print(tree)


    file_name = '/original_examples/list-equivelance.prql'
    text_all = read_file(file_name)
    for text in text_all.split('*******'):
        print('*' * 80)
        print(f'Parsing {file_name}\n' + '*' * 80)
        print(text)
        print('-' * 80)
        tree = parse(text)
        print('AST: pretty_print(tree)')
        print('-' * 80)

        pretty_print(tree)
    file_name = '/original_examples/scratch.prql'
    text = read_file(file_name)
    print('*' * 80)
    print(f'Parsing {file_name}\n' + '*' * 80 )
    print(text)
    print('-' * 80)
    tree = parse(text)
    print('AST: pretty_print(tree)')
    print('-' * 80)

    file_name =  '/original_examples/variables.prql'
    text = read_file(file_name)
    print('*' * 80)
    print(f'Parsing {file_name}\n' + '*' * 80 )
    print(text)
    print('-' * 80)
    tree = parse(read_file(file_name))
    print('AST: pretty_print(tree)')
    print('-' * 80)

    pretty_print(tree)
    print(tree_to_sql(tree))
    pretty_print(tree)