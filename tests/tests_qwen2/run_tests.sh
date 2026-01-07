#!/bin/bash

# Script to run all dynamic route tests

echo "Running Dynamic Route Tests..."
echo "================================"

# Set environment to use local test configuration
export ENV_FILE_LOCATION="/workspace/tests/.env.tests.local"

# Run tests with different configurations
echo "1. Running route discovery tests..."
python -m pytest tests/tests_qwen2/test_route_discovery.py -v

echo ""
echo "2. Running route validation tests..."
python -m pytest tests/tests_qwen2/test_route_validation.py -v

echo ""
echo "3. Running route analysis tests..."
python -m pytest tests/tests_qwen2/test_routes_analysis.py -v

echo ""
echo "4. Running comprehensive route tests..."
python -m pytest tests/tests_qwen2/test_comprehensive_routes.py -v

echo ""
echo "5. Running dynamic route tests with mocks (fast)..."
python -m pytest tests/tests_qwen2/test_all_routes_dynamic_mock.py -v

echo ""
echo "All tests completed!"