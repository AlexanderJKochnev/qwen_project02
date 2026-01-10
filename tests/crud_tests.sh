#!/bin/bash

python -m pytest tests/tests_crud/test_create.py \
                 tests/tests_crud/test_delete.py \
                 -v --tb=short