# Testing

Broadly speaking,
our tests are grouped into two categories:

1. Tests that make sure parsing and SQL generation of individual features work correctly (ie. unit tests).
1. Tests that perform full example queries (ie. integration tests)

## Unit Tests

There are currently 5 unit test modules:

1. [test_functions](./test_functions.md) which checks that functions are used correctly.
1. [test_grammar](./test_grammar.md) which checks that various elements of the grammar are handled correctly.
1. [test_stdlib](./test_stdlib.md) which checks that standard operations (sum, min, max, etc.) perform as expected.
1. [test_sql_generator](./test_sql_generator.md) which checks SQL is generated correctly from PRQL.
1. [test_prql_util_functions](./test_prql_util_functions.md) which checks that helper functions for parsing perform as expected.

```{toctree}
:hidden:
:maxdepth: 3

test_functions
test_grammar
test_stdlib
test_sql_generator
test_prql_util_functions
```

## Integration Tests

There are currently 2 integration test modules:

1. [test_employee_examples](./test_employee_examples.md)
1. [test_factbook_examples](./test_factbook_examples.md)

Both perform some complete queries on the sample database in their module name.

```{toctree}
:hidden:
:maxdepth: 3

test_employee_examples
test_factbook_examples
```
