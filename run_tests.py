#!/usr/bin/env python3
"""
Test runner for the Cloud Storage Tiering System assignment.

This script provides a convenient way to run different test suites and generate reports.
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
ALLURE_RESULTS_DIR = REPORTS_DIR / "allure-results"
COVERAGE_DIR = REPORTS_DIR / "coverage"
BENCHMARK_FILE = REPORTS_DIR / "benchmark.json"

def run_tests(test_type, verbose=False, coverage=False, allure=False, benchmark=False):
    """Run the specified test suite."""
    cmd = ["pytest", "-v" if verbose else "-q"]
    
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term",
            "--cov-report=xml:coverage.xml"
        ])

    if allure:
        cmd.append(f"--benchmark-json={BENCHMARK_FILE}")
    
    if test_type == "all":
        cmd.append("tests/")
    elif test_type == "functional":
        cmd.append("tests/functional/")
    elif test_type == "performance":
        cmd.append("tests/performance/")
    elif test_type == "fault":
        cmd.append("tests/fault_injection/")
    else:
        print(f"Unknown test type: {test_type}")
        return False
    
    print(f"Running {test_type} tests...")
    result = subprocess.run(cmd)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Run tests for the Cloud Storage Tiering System")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "functional", "performance", "fault"],
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--allure",
        action="store_true",
        help="Generate Allure report under reports/allure-results"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Generate benchmark report under reports/benchmark.json"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the correct directory
    os.chdir(Path(__file__).parent)
    
    success = run_tests(args.test_type, args.verbose, args.coverage, args.allure, args.benchmark)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
