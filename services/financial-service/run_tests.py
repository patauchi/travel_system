#!/usr/bin/env python3
"""
Financial Service Test Runner
Comprehensive test execution script for the modular financial service
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_banner(title):
    """Print a formatted banner"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def run_command(command, description="", timeout=300):
    """Run a command and return success status"""
    print_section(f"Running: {description or command}")
    print(f"Command: {command}")

    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project_root
        )

        execution_time = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ SUCCESS ({execution_time:.2f}s)")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
        else:
            print(f"❌ FAILED ({execution_time:.2f}s)")
            print("STDERR:")
            print(result.stderr)
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT after {timeout}s")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        return False, "", str(e)

def check_dependencies():
    """Check if required dependencies are installed"""
    print_banner("CHECKING DEPENDENCIES")

    dependencies = [
        ("python", "python --version"),
        ("pytest", "pytest --version"),
        ("sqlalchemy", "python -c 'import sqlalchemy; print(sqlalchemy.__version__)'"),
        ("fastapi", "python -c 'import fastapi; print(fastapi.__version__)'"),
        ("pydantic", "python -c 'import pydantic; print(pydantic.__version__)'"),
    ]

    all_good = True
    for name, command in dependencies:
        success, stdout, stderr = run_command(command, f"Checking {name}")
        if not success:
            all_good = False
            print(f"❌ {name} not found or not working")
        else:
            version = stdout.strip().split('\n')[-1]
            print(f"✅ {name}: {version}")

    return all_good

def setup_test_environment():
    """Setup test environment"""
    print_banner("SETTING UP TEST ENVIRONMENT")

    # Create test directories
    test_dirs = [
        "tests",
        "tests/__pycache__",
        "htmlcov",
        "logs"
    ]

    for dir_path in test_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(exist_ok=True)
        print(f"✅ Directory: {dir_path}")

    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/financial_test_db"
    os.environ["LOG_LEVEL"] = "INFO"

    print("✅ Environment variables set")
    return True

def run_unit_tests():
    """Run unit tests"""
    print_banner("RUNNING UNIT TESTS")

    command = "pytest tests/ -m 'not integration' -v --tb=short --durations=10"
    success, stdout, stderr = run_command(command, "Unit Tests")

    return success

def run_integration_tests():
    """Run integration tests"""
    print_banner("RUNNING INTEGRATION TESTS")

    command = "pytest tests/test_integration.py -v --tb=short --durations=10"
    success, stdout, stderr = run_command(command, "Integration Tests")

    return success

def run_module_specific_tests():
    """Run tests for specific modules"""
    print_banner("RUNNING MODULE-SPECIFIC TESTS")

    modules = [
        ("orders", "TestOrdersModule"),
        ("expenses", "TestExpensesModule"),
        ("pettycash", "TestPettyCashModule"),
        ("voucher", "TestVoucherModule"),
        ("invoices", "TestInvoicesModule"),
        ("payments", "TestPaymentsModule")
    ]

    results = {}
    for module_name, test_class in modules:
        print_section(f"Testing {module_name.title()} Module")
        command = f"pytest tests/test_integration.py::{test_class} -v"
        success, stdout, stderr = run_command(command, f"{module_name} module tests")
        results[module_name] = success

    return results

def run_coverage_report():
    """Generate coverage report"""
    print_banner("GENERATING COVERAGE REPORT")

    # Run tests with coverage
    command = "pytest tests/ --cov=. --cov-report=html:htmlcov --cov-report=term-missing --cov-exclude=tests/*"
    success, stdout, stderr = run_command(command, "Coverage Analysis")

    if success:
        print("✅ Coverage report generated in htmlcov/")

        # Try to open coverage report
        coverage_file = project_root / "htmlcov" / "index.html"
        if coverage_file.exists():
            print(f"📊 Coverage report: file://{coverage_file.absolute()}")

    return success

def run_performance_tests():
    """Run performance tests"""
    print_banner("RUNNING PERFORMANCE TESTS")

    command = "pytest tests/test_integration.py::TestPerformance -v --durations=0"
    success, stdout, stderr = run_command(command, "Performance Tests")

    return success

def run_health_checks():
    """Run health check tests"""
    print_banner("RUNNING HEALTH CHECKS")

    command = "pytest tests/test_integration.py::TestHealthChecks -v"
    success, stdout, stderr = run_command(command, "Health Check Tests")

    return success

def run_error_handling_tests():
    """Run error handling tests"""
    print_banner("RUNNING ERROR HANDLING TESTS")

    command = "pytest tests/test_integration.py::TestErrorHandling -v"
    success, stdout, stderr = run_command(command, "Error Handling Tests")

    return success

def run_cross_module_tests():
    """Run cross-module integration tests"""
    print_banner("RUNNING CROSS-MODULE INTEGRATION TESTS")

    command = "pytest tests/test_integration.py::TestCrossModuleIntegration -v --tb=long"
    success, stdout, stderr = run_command(command, "Cross-Module Integration Tests")

    return success

def generate_test_report(results):
    """Generate a comprehensive test report"""
    print_banner("TEST EXECUTION SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests

    print(f"📊 Total Test Suites: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")

    # Save report to file
    report_file = project_root / "test_report.txt"
    with open(report_file, "w") as f:
        f.write(f"Financial Service Test Report\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Total Test Suites: {total_tests}\n")
        f.write(f"Passed: {passed_tests}\n")
        f.write(f"Failed: {failed_tests}\n")
        f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")
        f.write("Detailed Results:\n")
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            f.write(f"  {status}: {test_name}\n")

    print(f"\n📄 Detailed report saved to: {report_file}")

    return passed_tests == total_tests

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Financial Service Test Runner")
    parser.add_argument("--quick", action="store_true", help="Run only quick tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--module", help="Run tests for specific module (orders, expenses, etc.)")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--health", action="store_true", help="Run health check tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-setup", action="store_true", help="Skip environment setup")

    args = parser.parse_args()

    print_banner("FINANCIAL SERVICE TEST RUNNER")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Project root: {project_root}")

    start_time = time.time()
    results = {}

    try:
        # Check dependencies
        if not check_dependencies():
            print("❌ Dependency check failed. Please install required packages.")
            return 1

        # Setup test environment
        if not args.no_setup:
            if not setup_test_environment():
                print("❌ Test environment setup failed.")
                return 1

        # Run specific test types based on arguments
        if args.quick:
            results["health_checks"] = run_health_checks()
            results["unit_tests"] = run_unit_tests()

        elif args.integration:
            results["integration_tests"] = run_integration_tests()
            results["cross_module_tests"] = run_cross_module_tests()

        elif args.unit:
            results["unit_tests"] = run_unit_tests()

        elif args.module:
            module_map = {
                "orders": "TestOrdersModule",
                "expenses": "TestExpensesModule",
                "pettycash": "TestPettyCashModule",
                "voucher": "TestVoucherModule",
                "invoices": "TestInvoicesModule",
                "payments": "TestPaymentsModule"
            }

            if args.module in module_map:
                command = f"pytest tests/test_integration.py::{module_map[args.module]} -v"
                success, _, _ = run_command(command, f"{args.module} module tests")
                results[f"{args.module}_module"] = success
            else:
                print(f"❌ Unknown module: {args.module}")
                print(f"Available modules: {', '.join(module_map.keys())}")
                return 1

        elif args.coverage:
            results["coverage_report"] = run_coverage_report()

        elif args.performance:
            results["performance_tests"] = run_performance_tests()

        elif args.health:
            results["health_checks"] = run_health_checks()

        else:
            # Run all tests
            results["dependencies"] = True  # Already checked
            results["health_checks"] = run_health_checks()
            results["unit_tests"] = run_unit_tests()
            results["integration_tests"] = run_integration_tests()

            # Module-specific tests
            module_results = run_module_specific_tests()
            results.update(module_results)

            results["cross_module_tests"] = run_cross_module_tests()
            results["error_handling_tests"] = run_error_handling_tests()
            results["performance_tests"] = run_performance_tests()

            if args.coverage or not args.quick:
                results["coverage_report"] = run_coverage_report()

        # Generate final report
        execution_time = time.time() - start_time
        print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")

        all_passed = generate_test_report(results)

        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
            return 0
        else:
            print("\n💥 SOME TESTS FAILED!")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
