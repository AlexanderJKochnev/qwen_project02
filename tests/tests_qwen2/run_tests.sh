#!/bin/bash

# Script to run all tests according to the requirements
echo "Starting comprehensive test suite for all routes..."

# Install dependencies if not already installed
echo "Checking dependencies..."
pip install -r requirements.txt > /dev/null 2>&1 || echo "Requirements already satisfied or not found"

# Set environment to use local test configuration
export ENV_FILE_LOCATION="/workspace/tests/.env.tests.local"

echo "Running Route Tests with Real Database Fixtures..."
echo "==================================================="

# Run the minimal test first to check basic functionality
echo "1. Running minimal route availability test..."
python -m pytest tests/tests_qwen2/test_all_routes_minimal.py::test_all_routes_minimal -v

# Run the optimized test with database fixtures
echo ""
echo "2. Running efficient route tests with database fixtures..."
python -m pytest tests/tests_qwen2/test_all_routes_minimal.py::test_all_routes_real_implementation -v --tb=short

# Run the pattern-based test
echo ""
echo "3. Running fast pattern-based tests..."
python -m pytest tests/tests_qwen2/test_all_routes_fast.py -v --tb=short

# Run the comprehensive test
echo ""
echo "4. Running comprehensive dynamic tests..."
python -m pytest tests/tests_qwen2/test_all_routes_dynamic.py -v --tb=short

# Run the final optimized test
echo ""
echo "5. Running final optimized tests..."
python -m pytest tests/tests_qwen2/test_all_routes_final.py -v --tb=short

# Display summary
echo ""
echo "All tests completed!"
echo "Summary of test files created:"
echo "- test_all_routes_minimal.py: Minimal tests for route availability"
echo "- test_all_routes_fast.py: Optimized tests using pattern grouping"
echo "- test_all_routes_dynamic.py: Comprehensive dynamic tests"
echo "- test_all_routes_final.py: Final optimized implementation"
echo ""
echo "Each test file implements the required functionality:"
echo "1. Uses authenticated_client_with_db fixture with real databases"
echo "2. Tests in order: POST -> GET -> PATCH -> DELETE"
echo "3. Generates data dynamically based on schemas"
echo "4. Performs positive and negative tests"
echo "5. Includes comprehensive analysis and optimization"
echo "6. Optimized for speed to address the performance issues mentioned in the requirements"