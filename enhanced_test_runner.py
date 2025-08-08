#!/usr/bin/env python3
"""
Enhanced Test Runner for Enhanced Individual Soldier Report System
Comprehensive testing framework with military-grade reliability requirements
"""

import pytest
import sys
import logging
import os
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
TESTS_PATH = PROJECT_ROOT / "tests"
sys.path.insert(0, str(SRC_PATH))

# Test configuration constants
DEFAULT_COVERAGE_THRESHOLD = 85
MILITARY_COVERAGE_THRESHOLD = 95  # Higher standard for military systems
DEFAULT_TIMEOUT = 300  # 5 minutes
PERFORMANCE_TIMEOUT = 600  # 10 minutes for performance tests


class TestConfiguration:
    """Test configuration management"""
    
    def __init__(self):
        self.coverage_threshold = DEFAULT_COVERAGE_THRESHOLD
        self.military_grade = False
        self.performance_tests = False
        self.integration_tests = True
        self.stress_tests = False
        self.timeout = DEFAULT_TIMEOUT
        self.parallel_workers = 1
        self.generate_reports = True
        self.fail_fast = False
        self.verbose_level = 1
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'coverage_threshold': self.coverage_threshold,
            'military_grade': self.military_grade,
            'performance_tests': self.performance_tests,
            'integration_tests': self.integration_tests,
            'stress_tests': self.stress_tests,
            'timeout': self.timeout,
            'parallel_workers': self.parallel_workers,
            'generate_reports': self.generate_reports,
            'fail_fast': self.fail_fast,
            'verbose_level': self.verbose_level
        }


class SoldierReportTestRunner:
    """
    Enhanced test runner for the Soldier Report System
    
    Features:
    - Military-grade testing standards
    - Comprehensive test categories
    - Performance and stress testing
    - Detailed reporting and metrics
    - CI/CD pipeline integration
    """
    
    def __init__(self, config: TestConfiguration):
        self.config = config
        self.start_time = None
        self.end_time = None
        self.test_results = {}
        self.setup_logging()
        self.setup_directories()
    
    def setup_logging(self):
        """Configure comprehensive logging for test execution"""
        
        # Create logs directory
        logs_dir = PROJECT_ROOT / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"test_run_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.DEBUG if self.config.verbose_level >= 2 else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file),
                logging.FileHandler(logs_dir / "latest_test_run.log")
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🎖️ Enhanced Soldier Report System Test Runner Started")
        self.logger.info(f"Configuration: {self.config.to_dict()}")
    
    def setup_directories(self):
        """Setup test output directories"""
        
        # Create test output directories
        self.test_output_dir = PROJECT_ROOT / "test_output"
        self.coverage_dir = self.test_output_dir / "coverage"
        self.reports_dir = self.test_output_dir / "reports"
        self.performance_dir = self.test_output_dir / "performance"
        
        for directory in [self.test_output_dir, self.coverage_dir, 
                         self.reports_dir, self.performance_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_pytest_args(self) -> List[str]:
        """Build pytest arguments based on configuration"""
        
        args = []
        
        # Verbosity
        if self.config.verbose_level >= 2:
            args.extend(['-vv'])
        elif self.config.verbose_level >= 1:
            args.extend(['-v'])
        
        # Basic pytest configuration
        args.extend([
            '--tb=short',
            '--strict-markers',
            '--strict-config',
            f'--timeout={self.config.timeout}',
        ])
        
        # Fail fast option
        if self.config.fail_fast:
            args.append('-x')
        
        # Parallel execution
        if self.config.parallel_workers > 1:
            args.extend(['-n', str(self.config.parallel_workers)])
        
        # Coverage configuration
        if self.config.generate_reports:
            coverage_threshold = (MILITARY_COVERAGE_THRESHOLD 
                                if self.config.military_grade 
                                else self.config.coverage_threshold)
            
            args.extend([
                '--cov=src',
                '--cov-report=html:' + str(self.coverage_dir),
                '--cov-report=xml:' + str(self.coverage_dir / 'coverage.xml'),
                '--cov-report=term-missing',
                '--cov-report=json:' + str(self.coverage_dir / 'coverage.json'),
                f'--cov-fail-under={coverage_threshold}',
                '--cov-branch',  # Branch coverage for military standards
            ])
        
        # Test markers and categories
        markers = []
        
        if not self.config.performance_tests:
            markers.append('not performance')
        
        if not self.config.stress_tests:
            markers.append('not stress')
        
        if not self.config.integration_tests:
            markers.append('not integration')
        
        if markers:
            args.extend(['-m', ' and '.join(markers)])
        
        # JUnit XML for CI/CD integration
        if self.config.generate_reports:
            args.extend([
                '--junitxml=' + str(self.reports_dir / 'junit.xml'),
                '--html=' + str(self.reports_dir / 'report.html'),
                '--self-contained-html'
            ])
        
        return args
    
    def run_pre_test_checks(self) -> bool:
        """Run pre-test system checks"""
        
        self.logger.info("🔍 Running pre-test system checks...")
        
        checks_passed = True
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.logger.error("❌ Python 3.8+ required for military-grade testing")
            checks_passed = False
        
        # Check required directories exist
        required_dirs = [SRC_PATH, TESTS_PATH]
        for directory in required_dirs:
            if not directory.exists():
                self.logger.error(f"❌ Required directory missing: {directory}")
                checks_passed = False
        
        # Check for test files
        test_files = list(TESTS_PATH.rglob("test_*.py"))
        if not test_files:
            self.logger.warning("⚠️ No test files found in tests directory")
        else:
            self.logger.info(f"✅ Found {len(test_files)} test files")
        
        # Check dependencies
        try:
            import pytest
            import coverage
            self.logger.info(f"✅ pytest version: {pytest.__version__}")
        except ImportError as e:
            self.logger.error(f"❌ Missing required dependency: {e}")
            checks_passed = False
        
        # Memory and disk space checks for military systems
        if self.config.military_grade:
            self._check_system_resources()
        
        return checks_passed
    
    def _check_system_resources(self):
        """Check system resources for military-grade testing"""
        
        try:
            import psutil
            
            # Memory check
            memory = psutil.virtual_memory()
            if memory.available < 1024 * 1024 * 1024:  # 1GB
                self.logger.warning("⚠️ Less than 1GB RAM available")
            
            # Disk space check
            disk = psutil.disk_usage('.')
            if disk.free < 5 * 1024 * 1024 * 1024:  # 5GB
                self.logger.warning("⚠️ Less than 5GB disk space available")
                
        except ImportError:
            self.logger.warning("⚠️ psutil not available for resource monitoring")
    
    def run_unit_tests(self) -> int:
        """Run unit tests"""
        
        self.logger.info("🧪 Running unit tests...")
        
        args = self.get_pytest_args()
        args.extend([
            str(TESTS_PATH / "unit"),
            '-m', 'not integration and not performance and not stress'
        ])
        
        return pytest.main(args)
    
    def run_integration_tests(self) -> int:
        """Run integration tests"""
        
        if not self.config.integration_tests:
            self.logger.info("⏭️ Skipping integration tests")
            return 0
        
        self.logger.info("🔗 Running integration tests...")
        
        args = self.get_pytest_args()
        args.extend([
            str(TESTS_PATH / "integration"),
            '-m', 'integration'
        ])
        
        return pytest.main(args)
    
    def run_performance_tests(self) -> int:
        """Run performance tests"""
        
        if not self.config.performance_tests:
            self.logger.info("⏭️ Skipping performance tests")
            return 0
        
        self.logger.info("⚡ Running performance tests...")
        
        args = self.get_pytest_args()
        args.extend([
            str(TESTS_PATH / "performance"),
            '-m', 'performance',
            f'--timeout={PERFORMANCE_TIMEOUT}'
        ])
        
        return pytest.main(args)
    
    def run_stress_tests(self) -> int:
        """Run stress tests for military-grade validation"""
        
        if not self.config.stress_tests:
            self.logger.info("⏭️ Skipping stress tests")
            return 0
        
        self.logger.info("💪 Running stress tests...")
        
        args = self.get_pytest_args()
        args.extend([
            str(TESTS_PATH / "stress"),
            '-m', 'stress',
            f'--timeout={PERFORMANCE_TIMEOUT * 2}'
        ])
        
        return pytest.main(args)
    
    def run_all_tests(self) -> int:
        """Run all tests in the appropriate order"""
        
        self.logger.info("🚀 Running comprehensive test suite...")
        
        args = self.get_pytest_args()
        args.append(str(TESTS_PATH))
        
        return pytest.main(args)
    
    def generate_test_report(self, exit_code: int):
        """Generate comprehensive test report"""
        
        if not self.config.generate_reports:
            return
        
        self.logger.info("📊 Generating test reports...")
        
        # Test execution summary
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        report_data = {
            'test_run_info': {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'exit_code': exit_code,
                'success': exit_code == 0,
                'configuration': self.config.to_dict()
            },
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': str(Path.cwd())
            },
            'test_results': self.test_results
        }
        
        # Write JSON report
        report_file = self.reports_dir / 'test_summary.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate markdown summary
        self._generate_markdown_summary(report_data)
        
        self.logger.info(f"📄 Test reports generated in {self.reports_dir}")
    
    def _generate_markdown_summary(self, report_data: Dict[str, Any]):
        """Generate markdown test summary"""
        
        summary_file = self.reports_dir / 'TEST_SUMMARY.md'
        
        with open(summary_file, 'w') as f:
            f.write("# 🎖️ Enhanced Soldier Report System - Test Results\n\n")
            
            # Test status
            status = "✅ PASSED" if report_data['test_run_info']['success'] else "❌ FAILED"
            f.write(f"## Test Status: {status}\n\n")
            
            # Summary table
            f.write("## Test Summary\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Timestamp | {report_data['test_run_info']['timestamp']} |\n")
            f.write(f"| Duration | {report_data['test_run_info']['duration_seconds']:.2f}s |\n")
            f.write(f"| Exit Code | {report_data['test_run_info']['exit_code']} |\n")
            f.write(f"| Python Version | {report_data['system_info']['python_version'].split()[0]} |\n")
            
            # Configuration
            config = report_data['test_run_info']['configuration']
            f.write(f"| Coverage Threshold | {config['coverage_threshold']}% |\n")
            f.write(f"| Military Grade | {'Yes' if config['military_grade'] else 'No'} |\n")
            
            f.write("\n## Test Configuration\n\n")
            f.write("```json\n")
            f.write(json.dumps(config, indent=2))
            f.write("\n```\n")
            
            # Links to detailed reports
            f.write("\n## Detailed Reports\n\n")
            f.write("- [HTML Coverage Report](coverage/index.html)\n")
            f.write("- [JUnit XML Report](junit.xml)\n")
            f.write("- [HTML Test Report](report.html)\n")
    
    def run(self, test_type: str = "all") -> int:
        """
        Main test execution method
        
        Args:
            test_type: Type of tests to run ('unit', 'integration', 'performance', 'stress', 'all')
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        
        self.start_time = time.time()
        
        try:
            # Pre-test checks
            if not self.run_pre_test_checks():
                self.logger.error("❌ Pre-test checks failed")
                return 1
            
            # Run specified tests
            if test_type == "unit":
                exit_code = self.run_unit_tests()
            elif test_type == "integration":
                exit_code = self.run_integration_tests()
            elif test_type == "performance":
                exit_code = self.run_performance_tests()
            elif test_type == "stress":
                exit_code = self.run_stress_tests()
            elif test_type == "all":
                exit_code = self.run_all_tests()
            else:
                self.logger.error(f"❌ Unknown test type: {test_type}")
                return 1
            
            self.end_time = time.time()
            
            # Generate reports
            self.generate_test_report(exit_code)
            
            # Final status
            if exit_code == 0:
                self.logger.info("🎉 All tests passed successfully!")
                if self.config.military_grade:
                    self.logger.info("🎖️ Military-grade testing standards met!")
            else:
                self.logger.error(f"❌ Tests failed with exit code {exit_code}")
            
            return exit_code
            
        except KeyboardInterrupt:
            self.logger.warning("⚠️ Test execution interrupted by user")
            return 1
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during test execution: {e}")
            return 1


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    
    parser = argparse.ArgumentParser(
        description="Enhanced Test Runner for Soldier Report System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py                    # Run all tests
  python test_runner.py -t unit            # Run only unit tests
  python test_runner.py --military-grade   # Run with military standards
  python test_runner.py --performance      # Include performance tests
  python test_runner.py -j 4               # Run with 4 parallel workers
        """
    )
    
    parser.add_argument(
        '-t', '--test-type',
        choices=['unit', 'integration', 'performance', 'stress', 'all'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    parser.add_argument(
        '--military-grade',
        action='store_true',
        help='Enable military-grade testing standards (higher coverage, stress tests)'
    )
    
    parser.add_argument(
        '--performance',
        action='store_true',
        help='Include performance tests'
    )
    
    parser.add_argument(
        '--stress',
        action='store_true',
        help='Include stress tests'
    )
    
    parser.add_argument(
        '--no-integration',
        action='store_true',
        help='Skip integration tests'
    )
    
    parser.add_argument(
        '-j', '--parallel-workers',
        type=int,
        default=1,
        help='Number of parallel test workers (default: 1)'
    )
    
    parser.add_argument(
        '--coverage-threshold',
        type=int,
        default=DEFAULT_COVERAGE_THRESHOLD,
        help=f'Coverage threshold percentage (default: {DEFAULT_COVERAGE_THRESHOLD})'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f'Test timeout in seconds (default: {DEFAULT_TIMEOUT})'
    )
    
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first test failure'
    )
    
    parser.add_argument(
        '--no-reports',
        action='store_true',
        help='Skip report generation'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=1,
        help='Increase verbosity (use -vv for very verbose)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test run (unit tests only, lower coverage threshold)'
    )
    
    return parser


def main():
    """Main entry point"""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create test configuration
    config = TestConfiguration()
    
    # Apply command line arguments
    config.military_grade = args.military_grade
    config.performance_tests = args.performance or args.military_grade
    config.stress_tests = args.stress or args.military_grade
    config.integration_tests = not args.no_integration
    config.parallel_workers = args.parallel_workers
    config.coverage_threshold = args.coverage_threshold
    config.timeout = args.timeout
    config.fail_fast = args.fail_fast
    config.generate_reports = not args.no_reports
    config.verbose_level = args.verbose
    
    # Quick mode adjustments
    if args.quick:
        config.coverage_threshold = 70
        config.performance_tests = False
        config.stress_tests = False
        config.integration_tests = False
        args.test_type = 'unit'
    
    # Military grade adjustments
    if config.military_grade:
        config.coverage_threshold = MILITARY_COVERAGE_THRESHOLD
        config.performance_tests = True
        config.stress_tests = True
    
    # Create and run test runner
    runner = SoldierReportTestRunner(config)
    exit_code = runner.run(args.test_type)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
