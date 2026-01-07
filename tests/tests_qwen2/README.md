# Dynamic Route Tests

This directory contains dynamic tests for all registered routes in the application.

## Test Structure

The main test file `test_all_routes_dynamic.py` performs comprehensive testing of all registered routes in the following order:

1. **POST routes**: Tests creation endpoints with positive and negative test cases
2. **GET routes**: Tests retrieval endpoints using data created in step 1
3. **PATCH routes**: Tests update endpoints using data created in step 1  
4. **DELETE routes**: Tests deletion endpoints using data created in step 1

## Key Features

- **Dynamic Route Discovery**: Automatically discovers all registered routes without hardcoding
- **Pydantic Schema Integration**: Uses Pydantic schemas to generate appropriate test data
- **Data Flow**: Created items are stored and reused for GET, PATCH, and DELETE operations
- **Comprehensive Testing**: Each route is tested with both positive and negative test cases
- **Result Summary**: Provides detailed summary of test results by method and status

## Test Execution Order

The tests follow the exact sequence specified in the requirements:
1. POST (create) - with expected positive result and negative test
2. GET (read) - with expected positive result and negative test  
3. PATCH (update) - with expected positive result and negative test
4. DELETE (remove) - with expected positive result and negative test

## Dependencies

The tests use the `authenticated_client_with_db` fixture from `conftest.py` which provides:
- Authenticated HTTP client
- Connection to PostgreSQL test database
- Connection to MongoDB test database

## Requirements

This test suite will connect to external databases when executed, so make sure:
- PostgreSQL server is accessible
- MongoDB server is accessible
- Environment variables are properly configured in the test environment

## Usage

```bash
# Run all dynamic route tests
pytest tests/tests_qwen2/test_all_routes_dynamic.py -v

# Run with detailed output
pytest tests/tests_qwen2/test_all_routes_dynamic.py -v -s
```