# File: tests/test_runner.py
"""Test runner script for the refactored system"""

import pytest
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_tests():
    """Run all tests with appropriate configuration"""
    
    # Configure logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_results.log')
        ]
    )
    
    # Test configuration
    pytest_args = [
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Strict marker checking
        '--cov=src',  # Coverage for src directory
        '--cov-report=html',  # HTML coverage report
        '--cov-report=term-missing',  # Terminal coverage report
        '--cov-fail-under=80',  # Fail if coverage below 80%
        'tests/',  # Test directory
    ]
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n🎉 All tests passed successfully!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)