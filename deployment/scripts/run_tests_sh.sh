#!/bin/bash
# File: deployment/scripts/run_tests.sh
# Test runner script

set -e

echo "🧪 Enhanced Soldier Report System - Test Suite"
echo "=============================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-cov
fi

# Create test reports directory
mkdir -p test_reports

# Run unit tests
echo "🔬 Running unit tests..."
python -m pytest tests/unit/ -v \
    --cov=src \
    --cov-report=html:test_reports/coverage_html \
    --cov-report=xml:test_reports/coverage.xml \
    --cov-report=term-missing \
    --junit-xml=test_reports/junit.xml

# Run integration tests
echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v \
    --junit-xml=test_reports/integration_junit.xml

# Performance tests (if any)
if [ -d "tests/performance" ]; then
    echo "⚡ Running performance tests..."
    python -m pytest tests/performance/ -v \
        --junit-xml=test_reports/performance_junit.xml
fi

echo ""
echo "✅ All tests completed!"
echo "📊 Coverage report: test_reports/coverage_html/index.html"
echo "📋 Test results: test_reports/junit.xml"