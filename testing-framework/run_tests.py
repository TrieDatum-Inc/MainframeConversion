#!/usr/bin/env python3
"""
CBTRN02C Migration Testing Framework - Main Test Runner

This script orchestrates the complete testing workflow:
1. Generate test data from test vectors
2. Run COBOL program (if GnuCOBOL available) to generate golden outputs
3. Run Spark pipeline with same inputs
4. Compare outputs and generate validation report

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --test TC001       # Run specific test
    python run_tests.py --spark-only       # Skip COBOL, compare with expected
    python run_tests.py --generate-only    # Only generate test data
    python run_tests.py --cobol-only       # Only run COBOL tests
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "test_data"))
sys.path.insert(0, str(Path(__file__).parent / "utils"))
sys.path.insert(0, str(Path(__file__).parent / "cobol_runner"))
sys.path.insert(0, str(Path(__file__).parent / "spark_runner"))

from test_data.test_vectors import get_all_test_vectors, get_test_vector_by_name, get_comprehensive_test_vector
from utils.file_generators import generate_test_files
from utils.comparator import (
    compare_cobol_spark_outputs, 
    compare_spark_with_expected,
    generate_comparison_report,
    ComparisonResult
)


def check_gnucobol_available() -> bool:
    """Check if GnuCOBOL is installed."""
    import subprocess
    try:
        result = subprocess.run(['cobc', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_pyspark_available() -> bool:
    """Check if PySpark is installed."""
    try:
        import pyspark
        return True
    except ImportError:
        return False


def generate_all_test_data(output_base_dir: str):
    """Generate test data for all test vectors."""
    print("\n" + "=" * 60)
    print("GENERATING TEST DATA")
    print("=" * 60)
    
    vectors = get_all_test_vectors()
    
    for tv in vectors:
        output_dir = Path(output_base_dir) / tv.name
        generate_test_files(tv, str(output_dir))
    
    # Also generate comprehensive test
    comprehensive = get_comprehensive_test_vector()
    generate_test_files(comprehensive, str(Path(output_base_dir) / comprehensive.name))
    
    print(f"\nGenerated test data for {len(vectors) + 1} test cases")
    return vectors


def run_cobol_tests(test_dirs: list, working_dir: str) -> dict:
    """Run COBOL tests and return results."""
    from cobol_runner.run_cobol import COBOLRunner
    
    print("\n" + "=" * 60)
    print("RUNNING COBOL TESTS")
    print("=" * 60)
    
    cobol_source_dir = str(Path(__file__).parent.parent / "app" / "cbl")
    copybook_dir = str(Path(__file__).parent.parent / "app" / "cpy")
    
    runner = COBOLRunner(
        cobol_source_dir=cobol_source_dir,
        copybook_dir=copybook_dir,
        working_dir=working_dir
    )
    
    # Compile once
    success, msg = runner.compile_program(force=True)
    if not success:
        print(f"COBOL compilation failed: {msg}")
        return {}
    
    print(f"COBOL compiled successfully")
    
    results = {}
    for test_dir in test_dirs:
        test_name = Path(test_dir).name
        print(f"\nRunning COBOL test: {test_name}")
        
        result = runner.run_test(test_dir)
        results[test_name] = result
        
        print(f"  Processed: {result.transactions_processed}")
        print(f"  Rejected: {result.transactions_rejected}")
        print(f"  Success: {result.success}")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
        
        # Parse outputs
        if result.success and result.output_files:
            rejects_file = result.output_files.get('DALYREJS.dat')
            if rejects_file:
                result.rejected_transactions = runner.parse_reject_output(rejects_file)
            
            trans_file = result.output_files.get('TRANFILE.dat')
            if trans_file:
                result.posted_transactions = runner.parse_transaction_output(trans_file)
    
    return results


def run_spark_tests(test_dirs: list) -> dict:
    """Run Spark tests and return results."""
    from spark_runner.run_spark import SparkCBTRN02CRunner
    
    print("\n" + "=" * 60)
    print("RUNNING SPARK TESTS")
    print("=" * 60)
    
    runner = SparkCBTRN02CRunner()
    
    results = {}
    for test_dir in test_dirs:
        test_name = Path(test_dir).name
        print(f"\nRunning Spark test: {test_name}")
        
        result = runner.run_test(test_dir)
        results[test_name] = result
        
        print(f"  Processed: {result.transactions_processed}")
        print(f"  Written: {result.transactions_written}")
        print(f"  Rejected: {result.transactions_rejected}")
        print(f"  Success: {result.success}")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
    
    runner.stop()
    return results


def compare_results(
    cobol_results: dict,
    spark_results: dict,
    test_dirs: list,
    spark_only: bool = False
) -> list:
    """Compare COBOL and Spark results."""
    print("\n" + "=" * 60)
    print("COMPARING RESULTS")
    print("=" * 60)
    
    comparison_results = []
    
    for test_dir in test_dirs:
        test_name = Path(test_dir).name
        expected_file = Path(test_dir) / "expected" / "results.json"
        
        spark_result = spark_results.get(test_name)
        
        if spark_result is None:
            print(f"\nSkipping {test_name}: No Spark result")
            continue
        
        if spark_only or test_name not in cobol_results:
            # Compare with expected values only
            if expected_file.exists():
                print(f"\nComparing {test_name} with expected values")
                comparison = compare_spark_with_expected(
                    test_name=test_name,
                    spark_result=spark_result,
                    expected_file=str(expected_file)
                )
            else:
                print(f"\nSkipping {test_name}: No expected file")
                continue
        else:
            # Compare COBOL vs Spark
            cobol_result = cobol_results[test_name]
            print(f"\nComparing {test_name}: COBOL vs Spark")
            comparison = compare_cobol_spark_outputs(
                test_name=test_name,
                cobol_result=cobol_result,
                spark_result=spark_result,
                expected_file=str(expected_file) if expected_file.exists() else None
            )
        
        comparison_results.append(comparison)
        
        status = "PASSED" if comparison.passed else "FAILED"
        print(f"  Status: {status}")
        print(f"  Checks: {comparison.passed_checks}/{comparison.total_checks} passed")
    
    return comparison_results


def main():
    parser = argparse.ArgumentParser(
        description="CBTRN02C Migration Testing Framework"
    )
    parser.add_argument(
        '--test', '-t',
        help='Run specific test by name (e.g., TC001_VALID_TRANSACTION)'
    )
    parser.add_argument(
        '--spark-only',
        action='store_true',
        help='Skip COBOL tests, compare Spark with expected values'
    )
    parser.add_argument(
        '--cobol-only',
        action='store_true',
        help='Only run COBOL tests'
    )
    parser.add_argument(
        '--generate-only',
        action='store_true',
        help='Only generate test data, do not run tests'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default=str(Path(__file__).parent / "golden_datasets"),
        help='Output directory for test data'
    )
    parser.add_argument(
        '--report-file', '-r',
        default=str(Path(__file__).parent / "test_report.txt"),
        help='Output file for test report'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CBTRN02C MIGRATION TESTING FRAMEWORK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check prerequisites
    gnucobol_available = check_gnucobol_available()
    pyspark_available = check_pyspark_available()
    
    print(f"\nPrerequisites:")
    print(f"  GnuCOBOL: {'Available' if gnucobol_available else 'Not installed'}")
    print(f"  PySpark: {'Available' if pyspark_available else 'Not installed'}")
    
    if not gnucobol_available and not args.spark_only:
        print("\nWarning: GnuCOBOL not available. Use --spark-only to test against expected values.")
        if not args.generate_only:
            args.spark_only = True
    
    if not pyspark_available and not args.cobol_only:
        print("\nError: PySpark not available. Install with: pip install pyspark")
        if not args.generate_only and not args.cobol_only:
            sys.exit(1)
    
    # Generate test data
    if args.test:
        # Single test
        tv = get_test_vector_by_name(args.test)
        if tv is None:
            print(f"\nError: Test '{args.test}' not found")
            print("Available tests:")
            for v in get_all_test_vectors():
                print(f"  - {v.name}")
            sys.exit(1)
        
        test_dir = Path(args.output_dir) / tv.name
        generate_test_files(tv, str(test_dir))
        test_dirs = [str(test_dir)]
    else:
        # All tests
        vectors = generate_all_test_data(args.output_dir)
        test_dirs = [str(Path(args.output_dir) / tv.name) for tv in vectors]
        # Add comprehensive test
        comprehensive = get_comprehensive_test_vector()
        test_dirs.append(str(Path(args.output_dir) / comprehensive.name))
    
    if args.generate_only:
        print("\nTest data generated. Exiting (--generate-only)")
        sys.exit(0)
    
    # Run tests
    cobol_results = {}
    spark_results = {}
    
    if not args.spark_only and gnucobol_available:
        working_dir = str(Path(__file__).parent / "cobol_runner")
        cobol_results = run_cobol_tests(test_dirs, working_dir)
    
    if not args.cobol_only and pyspark_available:
        spark_results = run_spark_tests(test_dirs)
    
    # Compare results
    if spark_results or cobol_results:
        comparison_results = compare_results(
            cobol_results=cobol_results,
            spark_results=spark_results,
            test_dirs=test_dirs,
            spark_only=args.spark_only
        )
        
        # Generate report
        if comparison_results:
            generate_comparison_report(comparison_results, args.report_file)
            print(f"\nReport written to: {args.report_file}")
            
            # Summary
            passed = sum(1 for r in comparison_results if r.passed)
            failed = len(comparison_results) - passed
            
            print("\n" + "=" * 60)
            print("FINAL SUMMARY")
            print("=" * 60)
            print(f"Total Tests: {len(comparison_results)}")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            
            if failed > 0:
                print("\nFailed tests:")
                for r in comparison_results:
                    if not r.passed:
                        print(f"  - {r.test_name}")
                sys.exit(1)
            else:
                print("\nAll tests passed!")
                sys.exit(0)
    else:
        print("\nNo test results to compare")
        sys.exit(1)


if __name__ == "__main__":
    main()
