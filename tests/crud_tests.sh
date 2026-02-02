#!/bin/bash

python -m pytest tests/tests_crud/test_routers.py \
                 tests/tests_crud/test_create.py \
                 tests/tests_crud/test_get.py \
                 tests/tests_crud/test_update.py \
                 -v --tb=short -s
                 # tests/tests_crud/test_delete.py \
                 # -v --tb=short -s