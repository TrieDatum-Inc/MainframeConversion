"""
CBTRN02C Test Data Generator

This module generates SQL INSERT statements and DataFrames for test data.
It can be used to:
1. Generate SQL files for loading test data into Databricks
2. Generate PySpark DataFrames for unit testing
3. Create isolated test environments for each test case
"""

from typing import List, Tuple
from decimal import Decimal
from datetime import datetime
import json

from test_cases import (
    TestCase, Account, CardXref, DailyTransaction,
    ALL_TEST_CASES, get_test_case_by_id
)


class TestDataGenerator:
    """Generates test data in various formats for CBTRN02C testing."""
    
    def __init__(self, database: str = "carddemo_test"):
        self.database = database
    
    def generate_sql_for_test_case(self, test_case: TestCase) -> str:
        """Generate complete SQL for a single test case."""
        sql_parts = []
        
        # Header comment
        sql_parts.append(f"-- Test Case: {test_case.test_id}")
        sql_parts.append(f"-- Description: {test_case.description}")
        sql_parts.append(f"-- Category: {test_case.category}")
        sql_parts.append(f"-- Generated: {datetime.now().isoformat()}")
        sql_parts.append("")
        
        # Clear existing test data
        sql_parts.append("-- Clear existing test data")
        sql_parts.append(f"DELETE FROM {self.database}.dalytran WHERE batch_id = '{test_case.test_id}';")
        sql_parts.append(f"DELETE FROM {self.database}.transactions WHERE batch_id = '{test_case.test_id}';")
        sql_parts.append(f"DELETE FROM {self.database}.transaction_rejects WHERE batch_id = '{test_case.test_id}';")
        sql_parts.append("")
        
        # Generate account inserts
        if test_case.accounts:
            sql_parts.append("-- Accounts")
            for acct in test_case.accounts:
                sql_parts.append(self._account_to_sql(acct))
            sql_parts.append("")
        
        # Generate card_xref inserts
        if test_case.card_xrefs:
            sql_parts.append("-- Card Cross-References")
            for xref in test_case.card_xrefs:
                sql_parts.append(self._card_xref_to_sql(xref))
            sql_parts.append("")
        
        # Generate transaction inserts
        if test_case.transactions:
            sql_parts.append("-- Daily Transactions")
            for tran in test_case.transactions:
                # Override batch_id with test_id for isolation
                tran.batch_id = test_case.test_id
                sql_parts.append(self._transaction_to_sql(tran))
            sql_parts.append("")
        
        return "\n".join(sql_parts)
    
    def _account_to_sql(self, acct: Account) -> str:
        """Convert Account to MERGE SQL (upsert)."""
        return f"""MERGE INTO {self.database}.accounts AS target
USING (SELECT '{acct.acct_id}' AS acct_id) AS source
ON target.acct_id = source.acct_id
WHEN MATCHED THEN UPDATE SET
    active_status = '{acct.active_status}',
    curr_bal = {acct.curr_bal},
    credit_limit = {acct.credit_limit},
    cash_credit_limit = {acct.cash_credit_limit},
    open_date = '{acct.open_date}',
    expiration_date = '{acct.expiration_date}',
    reissue_date = '{acct.reissue_date}',
    curr_cyc_credit = {acct.curr_cyc_credit},
    curr_cyc_debit = {acct.curr_cyc_debit},
    group_id = '{acct.group_id}'
WHEN NOT MATCHED THEN INSERT (
    acct_id, active_status, curr_bal, credit_limit, cash_credit_limit,
    open_date, expiration_date, reissue_date, curr_cyc_credit, curr_cyc_debit, group_id
) VALUES (
    '{acct.acct_id}', '{acct.active_status}', {acct.curr_bal}, {acct.credit_limit}, {acct.cash_credit_limit},
    '{acct.open_date}', '{acct.expiration_date}', '{acct.reissue_date}', {acct.curr_cyc_credit}, {acct.curr_cyc_debit}, '{acct.group_id}'
);"""
    
    def _card_xref_to_sql(self, xref: CardXref) -> str:
        """Convert CardXref to MERGE SQL (upsert)."""
        return f"""MERGE INTO {self.database}.card_xref AS target
USING (SELECT '{xref.card_num}' AS card_num) AS source
ON target.card_num = source.card_num
WHEN MATCHED THEN UPDATE SET
    acct_id = '{xref.acct_id}',
    cust_id = '{xref.cust_id}'
WHEN NOT MATCHED THEN INSERT (card_num, acct_id, cust_id)
VALUES ('{xref.card_num}', '{xref.acct_id}', '{xref.cust_id}');"""
    
    def _transaction_to_sql(self, tran: DailyTransaction) -> str:
        """Convert DailyTransaction to INSERT SQL."""
        return f"""INSERT INTO {self.database}.dalytran (
    tran_id, tran_type_cd, tran_cat_cd, tran_source, tran_desc,
    tran_amt, merchant_id, merchant_name, merchant_city, merchant_zip,
    card_num, orig_ts, batch_id, ingestion_ts
) VALUES (
    '{tran.tran_id}', '{tran.tran_type_cd}', {tran.tran_cat_cd}, '{tran.tran_source}', '{tran.tran_desc}',
    {tran.tran_amt}, {tran.merchant_id}, '{tran.merchant_name}', '{tran.merchant_city}', '{tran.merchant_zip}',
    '{tran.card_num}', '{tran.orig_ts}', '{tran.batch_id}', current_timestamp()
);"""
    
    def generate_all_test_sql(self, output_file: str = None) -> str:
        """Generate SQL for all test cases."""
        all_sql = []
        
        all_sql.append("-- " + "=" * 78)
        all_sql.append("-- CBTRN02C COMPREHENSIVE TEST DATA")
        all_sql.append(f"-- Generated: {datetime.now().isoformat()}")
        all_sql.append(f"-- Total Test Cases: {len(ALL_TEST_CASES)}")
        all_sql.append("-- " + "=" * 78)
        all_sql.append("")
        all_sql.append(f"USE {self.database};")
        all_sql.append("")
        
        for tc in ALL_TEST_CASES:
            all_sql.append("")
            all_sql.append("-- " + "=" * 78)
            all_sql.append(self.generate_sql_for_test_case(tc))
        
        result = "\n".join(all_sql)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(result)
            print(f"Generated SQL written to: {output_file}")
        
        return result
    
    def generate_pyspark_test_data(self, test_case: TestCase) -> dict:
        """
        Generate Python dictionaries for creating PySpark DataFrames.
        
        Returns:
            dict with keys: 'accounts', 'card_xrefs', 'transactions'
        """
        return {
            'accounts': [self._account_to_dict(a) for a in test_case.accounts],
            'card_xrefs': [self._card_xref_to_dict(x) for x in test_case.card_xrefs],
            'transactions': [self._transaction_to_dict(t, test_case.test_id) for t in test_case.transactions]
        }
    
    def _account_to_dict(self, acct: Account) -> dict:
        """Convert Account to dictionary."""
        return {
            'acct_id': acct.acct_id,
            'active_status': acct.active_status,
            'curr_bal': float(acct.curr_bal),
            'credit_limit': float(acct.credit_limit),
            'cash_credit_limit': float(acct.cash_credit_limit),
            'open_date': acct.open_date,
            'expiration_date': acct.expiration_date,
            'reissue_date': acct.reissue_date,
            'curr_cyc_credit': float(acct.curr_cyc_credit),
            'curr_cyc_debit': float(acct.curr_cyc_debit),
            'group_id': acct.group_id
        }
    
    def _card_xref_to_dict(self, xref: CardXref) -> dict:
        """Convert CardXref to dictionary."""
        return {
            'card_num': xref.card_num,
            'acct_id': xref.acct_id,
            'cust_id': xref.cust_id
        }
    
    def _transaction_to_dict(self, tran: DailyTransaction, batch_id: str) -> dict:
        """Convert DailyTransaction to dictionary."""
        return {
            'tran_id': tran.tran_id,
            'tran_type_cd': tran.tran_type_cd,
            'tran_cat_cd': tran.tran_cat_cd,
            'tran_source': tran.tran_source,
            'tran_desc': tran.tran_desc,
            'tran_amt': float(tran.tran_amt),
            'merchant_id': tran.merchant_id,
            'merchant_name': tran.merchant_name,
            'merchant_city': tran.merchant_city,
            'merchant_zip': tran.merchant_zip,
            'card_num': tran.card_num,
            'orig_ts': tran.orig_ts,
            'batch_id': batch_id
        }
    
    def generate_verification_sql(self, test_case: TestCase) -> str:
        """Generate SQL queries to verify test results."""
        sql_parts = []
        
        sql_parts.append(f"-- Verification queries for: {test_case.test_id}")
        sql_parts.append("")
        
        # Count transactions read
        sql_parts.append("-- 1. Transactions Read")
        sql_parts.append(f"SELECT COUNT(*) as transactions_read FROM {self.database}.dalytran WHERE batch_id = '{test_case.test_id}';")
        sql_parts.append(f"-- Expected: {test_case.expected.transactions_read}")
        sql_parts.append("")
        
        # Count transactions posted
        sql_parts.append("-- 2. Transactions Posted")
        sql_parts.append(f"SELECT COUNT(*) as transactions_posted FROM {self.database}.transactions WHERE batch_id = '{test_case.test_id}';")
        sql_parts.append(f"-- Expected: {test_case.expected.transactions_posted}")
        sql_parts.append("")
        
        # Count transactions rejected
        sql_parts.append("-- 3. Transactions Rejected")
        sql_parts.append(f"SELECT COUNT(*) as transactions_rejected FROM {self.database}.transaction_rejects WHERE batch_id = '{test_case.test_id}';")
        sql_parts.append(f"-- Expected: {test_case.expected.transactions_rejected}")
        sql_parts.append("")
        
        # Check reject codes
        if test_case.expected.reject_codes:
            sql_parts.append("-- 4. Reject Codes")
            sql_parts.append(f"""SELECT tran_id, reject_reason_code, reject_reason_desc 
FROM {self.database}.transaction_rejects 
WHERE batch_id = '{test_case.test_id}'
ORDER BY tran_id;""")
            sql_parts.append(f"-- Expected reject codes: {test_case.expected.reject_codes}")
            sql_parts.append(f"-- Expected reject tran_ids: {test_case.expected.reject_tran_ids}")
            sql_parts.append("")
        
        # Check posted transaction IDs
        if test_case.expected.posted_tran_ids:
            sql_parts.append("-- 5. Posted Transaction IDs")
            sql_parts.append(f"""SELECT tran_id 
FROM {self.database}.transactions 
WHERE batch_id = '{test_case.test_id}'
ORDER BY tran_id;""")
            sql_parts.append(f"-- Expected posted tran_ids: {test_case.expected.posted_tran_ids}")
            sql_parts.append("")
        
        # Check account balances
        if test_case.expected.expected_account_balances:
            sql_parts.append("-- 6. Account Balances")
            acct_ids = list(test_case.expected.expected_account_balances.keys())
            acct_list = "', '".join(acct_ids)
            sql_parts.append(f"""SELECT acct_id, curr_bal, curr_cyc_credit, curr_cyc_debit 
FROM {self.database}.accounts 
WHERE acct_id IN ('{acct_list}')
ORDER BY acct_id;""")
            for acct_id, expected_bal in test_case.expected.expected_account_balances.items():
                sql_parts.append(f"-- Expected {acct_id} curr_bal: {expected_bal}")
            sql_parts.append("")
        
        return "\n".join(sql_parts)
    
    def generate_json_test_data(self, test_case: TestCase) -> str:
        """Generate JSON representation of test data for documentation."""
        data = {
            'test_id': test_case.test_id,
            'description': test_case.description,
            'category': test_case.category,
            'notes': test_case.notes,
            'input': self.generate_pyspark_test_data(test_case),
            'expected': {
                'transactions_read': test_case.expected.transactions_read,
                'transactions_posted': test_case.expected.transactions_posted,
                'transactions_rejected': test_case.expected.transactions_rejected,
                'reject_codes': test_case.expected.reject_codes,
                'reject_tran_ids': test_case.expected.reject_tran_ids,
                'posted_tran_ids': test_case.expected.posted_tran_ids,
                'expected_account_balances': {
                    k: float(v) for k, v in test_case.expected.expected_account_balances.items()
                }
            }
        }
        return json.dumps(data, indent=2)


def generate_notebook_test_code(test_case: TestCase, database: str = "carddemo_test") -> str:
    """
    Generate Python code that can be run in a Databricks notebook to execute a test.
    """
    generator = TestDataGenerator(database)
    test_data = generator.generate_pyspark_test_data(test_case)
    
    code = f'''# Test Case: {test_case.test_id}
# Description: {test_case.description}
# Category: {test_case.category}

from pyspark.sql import SparkSession
from pyspark.sql.types import *
import sys
sys.path.append('/Workspace/Users/your-email/cbtrn02c_migration')
from cbtrn02c_job import CBTRN02CJob

spark = SparkSession.builder.getOrCreate()

# Test data
accounts_data = {test_data['accounts']}
card_xrefs_data = {test_data['card_xrefs']}
transactions_data = {test_data['transactions']}

# Create temporary views for test isolation
if accounts_data:
    spark.createDataFrame(accounts_data).createOrReplaceTempView("test_accounts")
    spark.sql(f"INSERT OVERWRITE {database}.accounts SELECT * FROM test_accounts")

if card_xrefs_data:
    spark.createDataFrame(card_xrefs_data).createOrReplaceTempView("test_card_xref")
    spark.sql(f"INSERT OVERWRITE {database}.card_xref SELECT * FROM test_card_xref")

if transactions_data:
    spark.createDataFrame(transactions_data).createOrReplaceTempView("test_dalytran")
    spark.sql(f"INSERT INTO {database}.dalytran SELECT *, current_timestamp() as ingestion_ts FROM test_dalytran")

# Run the job
job = CBTRN02CJob(
    spark=spark,
    database="{database}",
    batch_id="{test_case.test_id}"
)
stats = job.run()

# Verify results
print("\\n" + "=" * 60)
print("TEST RESULTS: {test_case.test_id}")
print("=" * 60)

expected_read = {test_case.expected.transactions_read}
expected_posted = {test_case.expected.transactions_posted}
expected_rejected = {test_case.expected.transactions_rejected}

actual_read = stats["records_read"]
actual_posted = stats["records_written"]
actual_rejected = stats["records_rejected"]

print(f"Transactions Read:     Expected={{expected_read}}, Actual={{actual_read}}, {{"PASS" if actual_read == expected_read else "FAIL"}}")
print(f"Transactions Posted:   Expected={{expected_posted}}, Actual={{actual_posted}}, {{"PASS" if actual_posted == expected_posted else "FAIL"}}")
print(f"Transactions Rejected: Expected={{expected_rejected}}, Actual={{actual_rejected}}, {{"PASS" if actual_rejected == expected_rejected else "FAIL"}}")

# Overall result
all_pass = (actual_read == expected_read and 
            actual_posted == expected_posted and 
            actual_rejected == expected_rejected)
print(f"\\nOVERALL: {{"PASS" if all_pass else "FAIL"}}")
'''
    return code


if __name__ == "__main__":
    # Generate SQL for all test cases
    generator = TestDataGenerator("carddemo_test")
    
    # Generate all test SQL
    generator.generate_all_test_sql("all_test_data.sql")
    
    # Generate verification SQL for each test
    print("\n" + "=" * 80)
    print("VERIFICATION SQL FOR EACH TEST CASE")
    print("=" * 80)
    
    for tc in ALL_TEST_CASES[:3]:  # Show first 3 as example
        print(f"\n{tc.test_id}:")
        print("-" * 40)
        print(generator.generate_verification_sql(tc))
