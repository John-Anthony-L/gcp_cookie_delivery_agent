#!/usr/bin/env python3
"""
Test runner for BigQuery ADK tools.
Runs both unit tests and integration tests with comprehensive reporting.
"""

import sys
import subprocess
import os
from datetime import datetime

def run_test_file(test_file, test_type):
    """Run a test file and return the results."""
    print(f"\n{'='*60}")
    print(f"Running {test_type} Tests: {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False, "", str(e)

def extract_test_stats(output):
    """Extract test statistics from test output."""
    lines = output.split('\n')
    stats = {}
    
    for line in lines:
        if 'Tests run:' in line:
            # Parse "Tests run: X" format
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'run:':
                    stats['total'] = int(parts[i+1])
                elif part == 'Failures:':
                    stats['failures'] = int(parts[i+1])
                elif part == 'Errors:':
                    stats['errors'] = int(parts[i+1])
        elif 'Ran ' in line and ' tests in ' in line:
            # Parse "Ran X tests in Y.ZZZs" format
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                stats['total'] = int(parts[1])
                if 'failures' not in stats:
                    stats['failures'] = 0
                if 'errors' not in stats:
                    stats['errors'] = 0
    
    if 'total' in stats:
        stats['passed'] = stats['total'] - stats.get('failures', 0) - stats.get('errors', 0)
        stats['success_rate'] = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
    
    return stats

def main():
    """Run all BigQuery ADK tests."""
    print("BigQuery ADK Test Suite Runner")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Define test files
    test_files = [
        ("test_adk_bigquery_unit.py", "Unit"),
        ("test_adk_integration.py", "Integration"),
    ]
    
    # Track overall results
    all_passed = True
    total_stats = {
        'total': 0,
        'passed': 0,
        'failures': 0,
        'errors': 0
    }
    test_results = []
    
    # Run each test file
    for test_file, test_type in test_files:
        if os.path.exists(test_file):
            passed, stdout, stderr = run_test_file(test_file, test_type)
            stats = extract_test_stats(stdout)
            
            test_results.append({
                'file': test_file,
                'type': test_type,
                'passed': passed,
                'stats': stats,
                'stdout': stdout,
                'stderr': stderr
            })
            
            if not passed:
                all_passed = False
            
            # Add to total stats
            if stats:
                total_stats['total'] += stats.get('total', 0)
                total_stats['passed'] += stats.get('passed', 0)
                total_stats['failures'] += stats.get('failures', 0)
                total_stats['errors'] += stats.get('errors', 0)
        else:
            print(f"\nWarning: Test file {test_file} not found")
            all_passed = False
    
    # Print comprehensive summary
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    
    for result in test_results:
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        stats = result['stats']
        
        print(f"\n{result['type']} Tests ({result['file']}): {status}")
        if stats:
            print(f"  Total: {stats.get('total', 'N/A')}")
            print(f"  Passed: {stats.get('passed', 'N/A')}")
            print(f"  Failures: {stats.get('failures', 'N/A')}")
            print(f"  Errors: {stats.get('errors', 'N/A')}")
            print(f"  Success Rate: {stats.get('success_rate', 0):.1f}%")
    
    # Overall statistics
    print(f"\n{'-'*40}")
    print("OVERALL STATISTICS")
    print(f"{'-'*40}")
    print(f"Total Tests: {total_stats['total']}")
    print(f"Passed: {total_stats['passed']}")
    print(f"Failed: {total_stats['failures']}")
    print(f"Errors: {total_stats['errors']}")
    
    if total_stats['total'] > 0:
        overall_success_rate = (total_stats['passed'] / total_stats['total']) * 100
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
    else:
        overall_success_rate = 0
        print("Overall Success Rate: N/A")
    
    # Final verdict
    print(f"\n{'='*80}")
    if all_passed and overall_success_rate >= 90:
        print("🎉 ALL TESTS PASSED! BigQuery ADK integration is working correctly.")
        verdict = "EXCELLENT"
    elif overall_success_rate >= 80:
        print("✅ Most tests passed. Some minor issues may need attention.")
        verdict = "GOOD"
    elif overall_success_rate >= 60:
        print("⚠️  Some tests failed. Please review the issues above.")
        verdict = "NEEDS_ATTENTION"
    else:
        print("❌ Many tests failed. Please address the critical issues.")
        verdict = "CRITICAL"
    
    print(f"Test Quality: {verdict}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Recommendations
    if not all_passed:
        print("\nRECOMMENDations:")
        print("1. Review failed tests and fix any application logic issues")
        print("2. Ensure all mocks properly simulate ADK behavior")
        print("3. Update tests when ADK interfaces change")
        print("4. Consider adding more edge case tests")
    else:
        print("\nNext Steps:")
        print("1. Consider adding more comprehensive test cases")
        print("2. Set up continuous integration with these tests")
        print("3. Monitor ADK updates for breaking changes")
        print("4. Add performance benchmarking tests")
    
    # Exit with appropriate code
    exit_code = 0 if all_passed else 1
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
