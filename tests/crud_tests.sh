#!/bin/bash

python -m pytest tests/tests_crud/test_routers.py \
                 tests/tests_crud/test_create.py \
                 tests/tests_crud/test_get.py \
                 -v --tb=short -s