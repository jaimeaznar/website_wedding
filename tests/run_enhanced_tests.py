# run_enhanced_tests.py
"""
Script to run the enhanced test suite with organized output.
"""
import subprocess
import sys
import time

def run_test_suite(test_file, description):
    """Run a specific test suite and display results."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Run the tests
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
        capture_output=True,
        text=True
    )
    
    duration = time.time() - start_time
    
    # Print output
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Print summary
    print(f"\n{description} completed in {duration:.2f}s")
    print(f"Exit code: {result.returncode}")
    
    return result.returncode == 0

def main():
    """Run all enhanced test suites."""
    print("Running Enhanced Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Run each test suite
    test_suites = [
        ('tests/test_performance.py', 'Performance Benchmarks'),
        ('tests/test_edge_cases.py', 'Edge Case Tests'),
        ('tests/test_email.py', 'Email Tests with Mocking'),
        ('tests/test_api_contracts.py', 'API Contract Tests'),
    ]
    
    for test_file, description in test_suites:
        passed = run_test_suite(test_file, description)
        all_passed = all_passed and passed
        
        if not passed:
            print(f"\n⚠️  {description} had failures!")
    
    # Run coverage report for new tests
    print(f"\n{'='*60}")
    print("Running Coverage Report for Enhanced Tests")
    print(f"{'='*60}")
    
    coverage_cmd = [
        sys.executable, '-m', 'pytest',
        'tests/test_performance.py',
        'tests/test_edge_cases.py', 
        'tests/test_email.py',
        'tests/test_api_contracts.py',
        '--cov=app',
        '--cov-report=term-missing'
    ]
    
    subprocess.run(coverage_cmd)
    
    # Final summary
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ All enhanced tests passed!")
    else:
        print("❌ Some tests failed. Please review the output above.")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()