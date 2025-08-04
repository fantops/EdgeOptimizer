#!/usr/bin/env python3
"""
Test Runner for EdgeOptimizer
Runs all test suites and provides summary
"""

import sys
import os
import unittest
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Run all test suites"""
    print("🚀 EdgeOptimizer Test Suite")
    print("=" * 60)
    print("Testing power comparison platform components...")
    print()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        print("🎯 EdgeOptimizer is ready for power comparison experiments")
    else:
        print("❌ SOME TESTS FAILED")
        if result.failures:
            print(f"💥 Failures: {len(result.failures)}")
        if result.errors:
            print(f"🔥 Errors: {len(result.errors)}")
        print("🔧 Please fix issues before proceeding")
    
    print(f"📈 Tests run: {result.testsRun}")
    print(f"⏱️  Duration: {end_time - start_time:.2f} seconds")
    
    if not result.wasSuccessful():
        print("\n🔍 FAILURE DETAILS:")
        for test, traceback in result.failures + result.errors:
            print(f"\n❌ {test}")
            print("-" * 40)
            print(traceback)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
