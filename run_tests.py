#!/usr/bin/env python3
"""Test runner for achieving 68%+ coverage."""

import os
import sys
import subprocess
import webbrowser

def run_tests_with_coverage():
    """Run tests with coverage targeting 68%."""
    print("🎯 Running Tests for 68%+ Coverage")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--cov=.",
        "--cov-report=term",
        "--cov-report=html",
        "--cov-fail-under=68",
        "--tb=short",
        "--durations=10"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    # Show coverage summary
    for line in result.stdout.split('\n'):
        if "TOTAL" in line:
            print(f"\n📊 COVERAGE SUMMARY: {line.strip()}")
    
    # Open HTML report if successful
    if result.returncode == 0 and os.path.exists("htmlcov/index.html"):
        print("\n📁 Opening coverage report...")
        webbrowser.open("file://" + os.path.abspath("htmlcov/index.html"))
    
    return result.returncode

def main():
    """Main function."""
    print("🚀 Appointment System Test Runner")
    print("Target: 68%+ Code Coverage")
    print("=" * 60)
    
    result = run_tests_with_coverage()
    
    if result == 0:
        print("\n🎉 Success! Achieved at least 68% coverage!")
    else:
        print("\n💥 Failed to reach 68% coverage")
    
    return result

if __name__ == "__main__":
    sys.exit(main())