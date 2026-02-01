#!/usr/bin/env python3
"""
CBTRN02C Test Runner

This script runs the comprehensive test suite for the CBTRN02C PySpark migration.
It can be run:
1. Locally with PySpark installed
2. In a Databricks notebook
3. Via spark-submit

Usage:
    python run_tests.py [--test-id TEST_ID] [--category CATEGORY] [--database DATABASE]
    
    # Run all tests
    python run_tests.py
    
    # Run specific test
    python run_tests.py --test-id TC_100_INVALID_CARD
    
    # Run tests by category
    python run_tests.py --category "Validation Rules"
"""

import argparse
import sys
import os
from datetime import datetime
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_cases import (
    TestCase, ALL_TEST_CASES, get_test_case_by_id, get_test_cases_by_category
)
from test_data_generator import TestDataGenerator


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_id: str
    description: str
    category: str
    passed: bool
    expected_read: int
    actual_read: int
    expected_posted: int
    actual_posted: int
    expected_rejected: int
    actual_rejected: int
    expected_reject_codes: List[int]
    actual_reject_codes: List[int]
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


class CBTRN02CTestRunner:
    """
    Test runner for CBTRN02C PySpark migration.
    
    This runner:
    1. Sets up test data for each test case
    2. Executes the CBTRN02C job
    3. Verifies results against expected outcomes
    4. Generates a test report
    """
    
    def __init__(self, spark=None, database: str = "carddemo_test"):
        self.spark = spark
        self.database = database
        self.generator = TestDataGenerator(database)
        self.results: List[TestResult] = []
        
        # Import job class
        try:
            from cbtrn02c_job import CBTRN02CJob
            self.job_class = CBTRN02CJob
        except ImportError:
            # Try relative import
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from cbtrn02c_job import CBTRN02CJob
            self.job_class = CBTRN02CJob
    
    def setup_spark(self):
        """Initialize Spark session if not provided."""
        if self.spark is None:
            try:
                from pyspark.sql import SparkSession
                self.spark = SparkSession.builder \
                    .appName("CBTRN02C_TestRunner") \
                    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                    .getOrCreate()
                print(f"Spark session initialized: {self.spark.version}")
            except Exception as e:
                print(f"ERROR: Could not initialize Spark session: {e}")
                print("Please run this in a Databricks notebook or with PySpark installed.")
                sys.exit(1)
    
    def setup_test_tables(self):
        """Create test database and tables if they don't exist."""
        print(f"\nSetting up test database: {self.database}")
        
        # Create database
        self.spark.sql(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        self.spark.sql(f"USE {self.database}")
        
        # Create tables (simplified schema for testing)
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {self.database}.accounts (
                acct_id STRING,
                active_status STRING,
                curr_bal DECIMAL(11,2),
                credit_limit DECIMAL(11,2),
                cash_credit_limit DECIMAL(11,2),
                open_date STRING,
                expiration_date STRING,
                reissue_date STRING,
                curr_cyc_credit DECIMAL(11,2),
                curr_cyc_debit DECIMAL(11,2),
                group_id STRING,
                last_updated_ts TIMESTAMP,
                last_updated_batch_id STRING
            ) USING DELTA
        """)
        
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {self.database}.card_xref (
                card_num STRING,
                acct_id STRING,
                cust_id STRING
            ) USING DELTA
        """)
        
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {self.database}.dalytran (
                tran_id STRING,
                tran_type_cd STRING,
                tran_cat_cd INT,
                tran_source STRING,
                tran_desc STRING,
                tran_amt DECIMAL(11,2),
                merchant_id BIGINT,
                merchant_name STRING,
                merchant_city STRING,
                merchant_zip STRING,
                card_num STRING,
                orig_ts STRING,
                proc_ts STRING,
                batch_id STRING,
                ingestion_ts TIMESTAMP
            ) USING DELTA
        """)
        
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {self.database}.transactions (
                tran_id STRING,
                tran_type_cd STRING,
                tran_cat_cd INT,
                tran_source STRING,
                tran_desc STRING,
                tran_amt DECIMAL(11,2),
                merchant_id BIGINT,
                merchant_name STRING,
                merchant_city STRING,
                merchant_zip STRING,
                card_num STRING,
                orig_ts STRING,
                proc_ts STRING,
                batch_id STRING,
                created_ts TIMESTAMP
            ) USING DELTA
        """)
        
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {self.database}.transaction_rejects (
                tran_id STRING,
                card_num STRING,
                tran_amt DECIMAL(11,2),
                orig_ts STRING,
                reject_reason_code INT,
                reject_reason_desc STRING,
                batch_id STRING,
                rejected_ts TIMESTAMP
            ) USING DELTA
        """)
        
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {self.database}.tran_cat_balance (
                acct_id STRING,
                tran_type_cd STRING,
                tran_cat_cd INT,
                tran_cat_bal DECIMAL(11,2),
                last_updated_ts TIMESTAMP,
                last_updated_batch_id STRING
            ) USING DELTA
        """)
        
        print("Test tables created successfully")
    
    def load_test_data(self, test_case: TestCase):
        """Load test data for a specific test case."""
        from pyspark.sql import functions as F
        
        # Clear previous test data for this batch
        self.spark.sql(f"DELETE FROM {self.database}.dalytran WHERE batch_id = '{test_case.test_id}'")
        self.spark.sql(f"DELETE FROM {self.database}.transactions WHERE batch_id = '{test_case.test_id}'")
        self.spark.sql(f"DELETE FROM {self.database}.transaction_rejects WHERE batch_id = '{test_case.test_id}'")
        
        # Load accounts (using MERGE for upsert)
        if test_case.accounts:
            accounts_data = self.generator.generate_pyspark_test_data(test_case)['accounts']
            if accounts_data:
                accounts_df = self.spark.createDataFrame(accounts_data)
                accounts_df.createOrReplaceTempView("temp_accounts")
                
                self.spark.sql(f"""
                    MERGE INTO {self.database}.accounts AS target
                    USING temp_accounts AS source
                    ON target.acct_id = source.acct_id
                    WHEN MATCHED THEN UPDATE SET
                        target.active_status = source.active_status,
                        target.curr_bal = source.curr_bal,
                        target.credit_limit = source.credit_limit,
                        target.cash_credit_limit = source.cash_credit_limit,
                        target.open_date = source.open_date,
                        target.expiration_date = source.expiration_date,
                        target.reissue_date = source.reissue_date,
                        target.curr_cyc_credit = source.curr_cyc_credit,
                        target.curr_cyc_debit = source.curr_cyc_debit,
                        target.group_id = source.group_id
                    WHEN NOT MATCHED THEN INSERT (
                        acct_id, active_status, curr_bal, credit_limit, cash_credit_limit,
                        open_date, expiration_date, reissue_date, curr_cyc_credit, curr_cyc_debit, group_id
                    ) VALUES (
                        source.acct_id, source.active_status, source.curr_bal, source.credit_limit, source.cash_credit_limit,
                        source.open_date, source.expiration_date, source.reissue_date, source.curr_cyc_credit, source.curr_cyc_debit, source.group_id
                    )
                """)
        
        # Load card_xref (using MERGE for upsert)
        if test_case.card_xrefs:
            xref_data = self.generator.generate_pyspark_test_data(test_case)['card_xrefs']
            if xref_data:
                xref_df = self.spark.createDataFrame(xref_data)
                xref_df.createOrReplaceTempView("temp_card_xref")
                
                self.spark.sql(f"""
                    MERGE INTO {self.database}.card_xref AS target
                    USING temp_card_xref AS source
                    ON target.card_num = source.card_num
                    WHEN MATCHED THEN UPDATE SET *
                    WHEN NOT MATCHED THEN INSERT *
                """)
        
        # Load transactions with explicit schema to avoid type inference issues
        if test_case.transactions:
            tran_data = self.generator.generate_pyspark_test_data(test_case)['transactions']
            if tran_data:
                from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DecimalType, LongType
                tran_schema = StructType([
                    StructField("tran_id", StringType(), True),
                    StructField("tran_type_cd", StringType(), True),
                    StructField("tran_cat_cd", IntegerType(), True),
                    StructField("tran_source", StringType(), True),
                    StructField("tran_desc", StringType(), True),
                    StructField("tran_amt", DecimalType(11, 2), True),
                    StructField("merchant_id", LongType(), True),
                    StructField("merchant_name", StringType(), True),
                    StructField("merchant_city", StringType(), True),
                    StructField("merchant_zip", StringType(), True),
                    StructField("card_num", StringType(), True),
                    StructField("orig_ts", StringType(), True),
                    StructField("batch_id", StringType(), True)
                ])
                tran_df = self.spark.createDataFrame(tran_data, schema=tran_schema)
                tran_df = tran_df.withColumn("ingestion_ts", F.current_timestamp())
                tran_df = tran_df.withColumn("proc_ts", F.lit(None).cast("string"))
                tran_df.write.format("delta").mode("append").saveAsTable(f"{self.database}.dalytran")
    
    def run_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case and return the result."""
        import time
        
        print(f"\n{'='*60}")
        print(f"Running: {test_case.test_id}")
        print(f"Description: {test_case.description}")
        print(f"{'='*60}")
        
        start_time = time.time()
        error_message = None
        actual_read = 0
        actual_posted = 0
        actual_rejected = 0
        actual_reject_codes = []
        
        try:
            # Load test data
            self.load_test_data(test_case)
            
            # Run the job
            job = self.job_class(
                spark=self.spark,
                database=self.database,
                batch_id=test_case.test_id
            )
            stats = job.run()
            
            # Get actual results
            actual_read = stats["records_read"]
            actual_posted = stats["records_written"]
            actual_rejected = stats["records_rejected"]
            
            # Get actual reject codes
            rejects_df = self.spark.sql(f"""
                SELECT reject_reason_code 
                FROM {self.database}.transaction_rejects 
                WHERE batch_id = '{test_case.test_id}'
                ORDER BY tran_id
            """)
            actual_reject_codes = [row.reject_reason_code for row in rejects_df.collect()]
            
        except Exception as e:
            error_message = str(e)
            print(f"ERROR: {error_message}")
        
        execution_time = (time.time() - start_time) * 1000
        
        # Determine if test passed
        passed = (
            error_message is None and
            actual_read == test_case.expected.transactions_read and
            actual_posted == test_case.expected.transactions_posted and
            actual_rejected == test_case.expected.transactions_rejected and
            actual_reject_codes == test_case.expected.reject_codes
        )
        
        result = TestResult(
            test_id=test_case.test_id,
            description=test_case.description,
            category=test_case.category,
            passed=passed,
            expected_read=test_case.expected.transactions_read,
            actual_read=actual_read,
            expected_posted=test_case.expected.transactions_posted,
            actual_posted=actual_posted,
            expected_rejected=test_case.expected.transactions_rejected,
            actual_rejected=actual_rejected,
            expected_reject_codes=test_case.expected.reject_codes,
            actual_reject_codes=actual_reject_codes,
            error_message=error_message,
            execution_time_ms=execution_time
        )
        
        # Print result
        status = "PASS" if passed else "FAIL"
        print(f"\nResult: {status}")
        print(f"  Read:     Expected={test_case.expected.transactions_read}, Actual={actual_read}")
        print(f"  Posted:   Expected={test_case.expected.transactions_posted}, Actual={actual_posted}")
        print(f"  Rejected: Expected={test_case.expected.transactions_rejected}, Actual={actual_rejected}")
        if test_case.expected.reject_codes:
            print(f"  Reject Codes: Expected={test_case.expected.reject_codes}, Actual={actual_reject_codes}")
        print(f"  Execution Time: {execution_time:.2f}ms")
        
        return result
    
    def run_all_tests(self, test_cases: List[TestCase] = None) -> List[TestResult]:
        """Run all test cases and return results."""
        if test_cases is None:
            test_cases = ALL_TEST_CASES
        
        print("\n" + "=" * 80)
        print("CBTRN02C TEST SUITE")
        print(f"Running {len(test_cases)} test cases")
        print(f"Database: {self.database}")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 80)
        
        self.setup_spark()
        self.setup_test_tables()
        
        self.results = []
        for tc in test_cases:
            result = self.run_test(tc)
            self.results.append(result)
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a test report in markdown format."""
        if not self.results:
            return "No test results available."
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        pass_rate = (passed / len(self.results)) * 100 if self.results else 0
        
        report = []
        report.append("# CBTRN02C Test Results Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now().isoformat()}")
        report.append(f"**Database:** {self.database}")
        report.append("")
        report.append("## Summary")
        report.append("")
        report.append(f"| Metric | Value |")
        report.append(f"|--------|-------|")
        report.append(f"| Total Tests | {len(self.results)} |")
        report.append(f"| Passed | {passed} |")
        report.append(f"| Failed | {failed} |")
        report.append(f"| Pass Rate | {pass_rate:.1f}% |")
        report.append("")
        
        # Results by category
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {'passed': 0, 'failed': 0}
            if r.passed:
                categories[r.category]['passed'] += 1
            else:
                categories[r.category]['failed'] += 1
        
        report.append("## Results by Category")
        report.append("")
        report.append("| Category | Passed | Failed | Pass Rate |")
        report.append("|----------|--------|--------|-----------|")
        for cat, counts in categories.items():
            total = counts['passed'] + counts['failed']
            rate = (counts['passed'] / total) * 100 if total > 0 else 0
            report.append(f"| {cat} | {counts['passed']} | {counts['failed']} | {rate:.1f}% |")
        report.append("")
        
        # Detailed results
        report.append("## Detailed Results")
        report.append("")
        report.append("| Test ID | Description | Status | Read | Posted | Rejected | Time (ms) |")
        report.append("|---------|-------------|--------|------|--------|----------|-----------|")
        
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            read_match = "OK" if r.expected_read == r.actual_read else f"{r.expected_read}/{r.actual_read}"
            posted_match = "OK" if r.expected_posted == r.actual_posted else f"{r.expected_posted}/{r.actual_posted}"
            rejected_match = "OK" if r.expected_rejected == r.actual_rejected else f"{r.expected_rejected}/{r.actual_rejected}"
            report.append(f"| {r.test_id} | {r.description[:40]}... | {status} | {read_match} | {posted_match} | {rejected_match} | {r.execution_time_ms:.0f} |")
        
        report.append("")
        
        # Failed tests details
        failed_tests = [r for r in self.results if not r.passed]
        if failed_tests:
            report.append("## Failed Tests Details")
            report.append("")
            for r in failed_tests:
                report.append(f"### {r.test_id}")
                report.append("")
                report.append(f"**Description:** {r.description}")
                report.append("")
                report.append("| Metric | Expected | Actual |")
                report.append("|--------|----------|--------|")
                report.append(f"| Transactions Read | {r.expected_read} | {r.actual_read} |")
                report.append(f"| Transactions Posted | {r.expected_posted} | {r.actual_posted} |")
                report.append(f"| Transactions Rejected | {r.expected_rejected} | {r.actual_rejected} |")
                report.append(f"| Reject Codes | {r.expected_reject_codes} | {r.actual_reject_codes} |")
                if r.error_message:
                    report.append(f"| Error | - | {r.error_message} |")
                report.append("")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "test_report.md"):
        """Save the test report to a file."""
        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)
        print(f"\nTest report saved to: {filename}")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="CBTRN02C Test Runner - Run comprehensive tests for the PySpark migration"
    )
    parser.add_argument(
        "--test-id", "-t",
        help="Run a specific test by ID (e.g., TC_100_INVALID_CARD)",
        default=None
    )
    parser.add_argument(
        "--category", "-c",
        help="Run tests by category (e.g., 'Validation Rules', 'Sequential Processing')",
        default=None
    )
    parser.add_argument(
        "--database", "-d",
        help="Database name for testing (default: carddemo_test)",
        default="carddemo_test"
    )
    parser.add_argument(
        "--report", "-r",
        help="Output file for test report (default: test_report.md)",
        default="test_report.md"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available test cases"
    )
    
    args = parser.parse_args()
    
    # List tests if requested
    if args.list:
        print("\nAvailable Test Cases:")
        print("=" * 80)
        categories = {}
        for tc in ALL_TEST_CASES:
            if tc.category not in categories:
                categories[tc.category] = []
            categories[tc.category].append(tc)
        
        for cat, tests in categories.items():
            print(f"\n{cat}:")
            print("-" * 40)
            for tc in tests:
                print(f"  {tc.test_id}: {tc.description[:50]}...")
        return
    
    # Determine which tests to run
    test_cases = None
    if args.test_id:
        tc = get_test_case_by_id(args.test_id)
        if tc:
            test_cases = [tc]
        else:
            print(f"ERROR: Test case '{args.test_id}' not found")
            sys.exit(1)
    elif args.category:
        test_cases = get_test_cases_by_category(args.category)
        if not test_cases:
            print(f"ERROR: No test cases found for category '{args.category}'")
            sys.exit(1)
    
    # Run tests
    runner = CBTRN02CTestRunner(database=args.database)
    results = runner.run_all_tests(test_cases)
    
    # Generate and save report
    runner.save_report(args.report)
    
    # Print summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETED")
    print("=" * 80)
    print(f"Total: {len(results)}, Passed: {passed}, Failed: {failed}")
    print(f"Pass Rate: {(passed/len(results)*100) if results else 0:.1f}%")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
