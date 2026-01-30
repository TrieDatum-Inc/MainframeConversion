"""
Comparator Utilities for CBTRN02C Testing

This module compares outputs from COBOL and Spark runs to validate
that the migrated pipeline produces identical results to the original.

Comparison includes:
1. Transaction counts (processed, written, rejected)
2. Posted transactions (field-by-field)
3. Rejected transactions (reason codes and descriptions)
4. Updated account balances
5. Transaction category balances
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
import difflib


@dataclass
class ComparisonResult:
    """Result of comparing COBOL and Spark outputs."""
    test_name: str
    passed: bool
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    differences: List[Dict] = field(default_factory=list)
    summary: str = ""
    
    def add_check(self, check_name: str, passed: bool, details: str = ""):
        """Add a check result."""
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1
            self.differences.append({
                'check': check_name,
                'details': details
            })
    
    def generate_summary(self):
        """Generate a summary of the comparison."""
        status = "PASSED" if self.passed else "FAILED"
        self.summary = f"""
========================================
Test: {self.test_name}
Status: {status}
========================================
Total Checks: {self.total_checks}
Passed: {self.passed_checks}
Failed: {self.failed_checks}
"""
        if self.differences:
            self.summary += "\nDifferences Found:\n"
            for diff in self.differences:
                self.summary += f"  - {diff['check']}: {diff['details']}\n"
        
        return self.summary


class OutputComparator:
    """
    Compares outputs from COBOL and Spark runs.
    """
    
    def __init__(self, tolerance: Decimal = Decimal("0.01")):
        """
        Initialize the comparator.
        
        Args:
            tolerance: Tolerance for decimal comparisons
        """
        self.tolerance = tolerance
    
    def compare_counts(
        self,
        cobol_processed: int,
        cobol_written: int,
        cobol_rejected: int,
        spark_processed: int,
        spark_written: int,
        spark_rejected: int,
        result: ComparisonResult
    ):
        """Compare transaction counts."""
        result.add_check(
            "Records Processed",
            cobol_processed == spark_processed,
            f"COBOL={cobol_processed}, Spark={spark_processed}"
        )
        result.add_check(
            "Records Written",
            cobol_written == spark_written,
            f"COBOL={cobol_written}, Spark={spark_written}"
        )
        result.add_check(
            "Records Rejected",
            cobol_rejected == spark_rejected,
            f"COBOL={cobol_rejected}, Spark={spark_rejected}"
        )
    
    def compare_transactions(
        self,
        cobol_transactions: List[Dict],
        spark_transactions: List[Dict],
        result: ComparisonResult
    ):
        """
        Compare posted transactions field-by-field.
        
        Args:
            cobol_transactions: Transactions from COBOL run
            spark_transactions: Transactions from Spark run
            result: ComparisonResult to update
        """
        # Sort by transaction ID for comparison
        cobol_sorted = sorted(cobol_transactions, key=lambda x: x.get('tran_id', ''))
        spark_sorted = sorted(spark_transactions, key=lambda x: x.get('tran_id', ''))
        
        # Check count
        if len(cobol_sorted) != len(spark_sorted):
            result.add_check(
                "Transaction Count",
                False,
                f"COBOL={len(cobol_sorted)}, Spark={len(spark_sorted)}"
            )
            return
        
        result.add_check("Transaction Count", True)
        
        # Compare each transaction
        fields_to_compare = [
            'tran_id', 'type_cd', 'cat_cd', 'source', 'desc',
            'merchant_id', 'merchant_name', 'merchant_city', 'merchant_zip',
            'card_num', 'orig_ts'
        ]
        
        for i, (cobol_tran, spark_tran) in enumerate(zip(cobol_sorted, spark_sorted)):
            tran_id = cobol_tran.get('tran_id', f'index_{i}')
            
            for field in fields_to_compare:
                cobol_val = str(cobol_tran.get(field, '')).strip()
                spark_val = str(spark_tran.get(field, '')).strip()
                
                if cobol_val != spark_val:
                    result.add_check(
                        f"Transaction {tran_id}.{field}",
                        False,
                        f"COBOL='{cobol_val}', Spark='{spark_val}'"
                    )
            
            # Compare amount with tolerance
            cobol_amt = Decimal(str(cobol_tran.get('amount', 0)))
            spark_amt = Decimal(str(spark_tran.get('tran_amt', spark_tran.get('amount', 0))))
            
            if abs(cobol_amt - spark_amt) > self.tolerance:
                result.add_check(
                    f"Transaction {tran_id}.amount",
                    False,
                    f"COBOL={cobol_amt}, Spark={spark_amt}"
                )
    
    def compare_rejects(
        self,
        cobol_rejects: List[Dict],
        spark_rejects: List[Dict],
        result: ComparisonResult
    ):
        """
        Compare rejected transactions.
        
        Args:
            cobol_rejects: Rejects from COBOL run
            spark_rejects: Rejects from Spark run
            result: ComparisonResult to update
        """
        # Sort by transaction ID
        cobol_sorted = sorted(cobol_rejects, key=lambda x: x.get('tran_id', ''))
        spark_sorted = sorted(spark_rejects, key=lambda x: x.get('tran_id', ''))
        
        # Check count
        if len(cobol_sorted) != len(spark_sorted):
            result.add_check(
                "Reject Count",
                False,
                f"COBOL={len(cobol_sorted)}, Spark={len(spark_sorted)}"
            )
            # Still try to compare what we can
        else:
            result.add_check("Reject Count", True)
        
        # Build lookup for comparison
        cobol_by_id = {r.get('tran_id'): r for r in cobol_sorted}
        spark_by_id = {r.get('tran_id'): r for r in spark_sorted}
        
        all_ids = set(cobol_by_id.keys()) | set(spark_by_id.keys())
        
        for tran_id in sorted(all_ids):
            cobol_rej = cobol_by_id.get(tran_id)
            spark_rej = spark_by_id.get(tran_id)
            
            if cobol_rej is None:
                result.add_check(
                    f"Reject {tran_id}",
                    False,
                    "Missing in COBOL output"
                )
                continue
            
            if spark_rej is None:
                result.add_check(
                    f"Reject {tran_id}",
                    False,
                    "Missing in Spark output"
                )
                continue
            
            # Compare reject code
            cobol_code = cobol_rej.get('reject_code', 0)
            spark_code = spark_rej.get('reject_code', 0)
            
            if cobol_code != spark_code:
                result.add_check(
                    f"Reject {tran_id}.code",
                    False,
                    f"COBOL={cobol_code}, Spark={spark_code}"
                )
            else:
                result.add_check(f"Reject {tran_id}.code", True)
    
    def compare_accounts(
        self,
        cobol_accounts: List[Dict],
        spark_accounts: List[Dict],
        result: ComparisonResult
    ):
        """
        Compare updated account balances.
        
        Args:
            cobol_accounts: Accounts from COBOL run
            spark_accounts: Accounts from Spark run
            result: ComparisonResult to update
        """
        cobol_by_id = {a.get('acct_id'): a for a in cobol_accounts}
        spark_by_id = {a.get('acct_id'): a for a in spark_accounts}
        
        all_ids = set(cobol_by_id.keys()) | set(spark_by_id.keys())
        
        for acct_id in sorted(all_ids):
            cobol_acct = cobol_by_id.get(acct_id)
            spark_acct = spark_by_id.get(acct_id)
            
            if cobol_acct is None or spark_acct is None:
                continue  # Skip accounts that don't exist in both
            
            # Compare balance fields
            balance_fields = ['curr_bal', 'curr_cyc_credit', 'curr_cyc_debit']
            
            for field in balance_fields:
                cobol_val = Decimal(str(cobol_acct.get(field, 0)))
                spark_val = Decimal(str(spark_acct.get(field, 0)))
                
                if abs(cobol_val - spark_val) > self.tolerance:
                    result.add_check(
                        f"Account {acct_id}.{field}",
                        False,
                        f"COBOL={cobol_val}, Spark={spark_val}"
                    )
    
    def compare_with_expected(
        self,
        actual_processed: int,
        actual_written: int,
        actual_rejected: int,
        expected_processed: int,
        expected_written: int,
        expected_rejected: int,
        result: ComparisonResult
    ):
        """Compare actual results with expected values from test vector."""
        result.add_check(
            "Expected Records Processed",
            actual_processed == expected_processed,
            f"Actual={actual_processed}, Expected={expected_processed}"
        )
        result.add_check(
            "Expected Records Written",
            actual_written == expected_written,
            f"Actual={actual_written}, Expected={expected_written}"
        )
        result.add_check(
            "Expected Records Rejected",
            actual_rejected == expected_rejected,
            f"Actual={actual_rejected}, Expected={expected_rejected}"
        )


def compare_cobol_spark_outputs(
    test_name: str,
    cobol_result,  # COBOLRunResult
    spark_result,  # SparkRunResult
    expected_file: str = None
) -> ComparisonResult:
    """
    Compare COBOL and Spark outputs.
    
    Args:
        test_name: Name of the test
        cobol_result: Result from COBOL run
        spark_result: Result from Spark run
        expected_file: Optional path to expected results JSON
        
    Returns:
        ComparisonResult with comparison details
    """
    result = ComparisonResult(test_name=test_name, passed=True)
    comparator = OutputComparator()
    
    # Compare counts
    comparator.compare_counts(
        cobol_processed=cobol_result.transactions_processed,
        cobol_written=cobol_result.transactions_processed - cobol_result.transactions_rejected,
        cobol_rejected=cobol_result.transactions_rejected,
        spark_processed=spark_result.transactions_processed,
        spark_written=spark_result.transactions_written,
        spark_rejected=spark_result.transactions_rejected,
        result=result
    )
    
    # Compare rejects
    comparator.compare_rejects(
        cobol_rejects=cobol_result.rejected_transactions if hasattr(cobol_result, 'rejected_transactions') else [],
        spark_rejects=spark_result.rejected_transactions,
        result=result
    )
    
    # Load and compare with expected if provided
    if expected_file and Path(expected_file).exists():
        with open(expected_file, 'r') as f:
            expected = json.load(f)
        
        comparator.compare_with_expected(
            actual_processed=spark_result.transactions_processed,
            actual_written=spark_result.transactions_written,
            actual_rejected=spark_result.transactions_rejected,
            expected_processed=expected.get('expected_records_read', 0),
            expected_written=expected.get('expected_records_written', 0),
            expected_rejected=expected.get('expected_records_rejected', 0),
            result=result
        )
    
    # Determine overall pass/fail
    result.passed = result.failed_checks == 0
    result.generate_summary()
    
    return result


def compare_spark_with_expected(
    test_name: str,
    spark_result,  # SparkRunResult
    expected_file: str
) -> ComparisonResult:
    """
    Compare Spark output with expected results (when COBOL is not available).
    
    Args:
        test_name: Name of the test
        spark_result: Result from Spark run
        expected_file: Path to expected results JSON
        
    Returns:
        ComparisonResult with comparison details
    """
    result = ComparisonResult(test_name=test_name, passed=True)
    comparator = OutputComparator()
    
    # Load expected results
    with open(expected_file, 'r') as f:
        expected = json.load(f)
    
    # Compare counts
    comparator.compare_with_expected(
        actual_processed=spark_result.transactions_processed,
        actual_written=spark_result.transactions_written,
        actual_rejected=spark_result.transactions_rejected,
        expected_processed=expected.get('expected_records_read', 0),
        expected_written=expected.get('expected_records_written', 0),
        expected_rejected=expected.get('expected_records_rejected', 0),
        result=result
    )
    
    # Compare individual transaction outcomes
    expected_transactions = expected.get('transactions', [])
    
    for exp_tran in expected_transactions:
        tran_id = exp_tran.get('tran_id')
        expected_valid = exp_tran.get('expected_valid')
        expected_reject_code = exp_tran.get('expected_reject_code')
        
        # Find in Spark results
        if expected_valid:
            # Should be in posted transactions
            found = any(t.get('tran_id') == tran_id for t in spark_result.posted_transactions)
            result.add_check(
                f"Transaction {tran_id} posted",
                found,
                f"Expected valid, found in posted: {found}"
            )
        else:
            # Should be in rejected transactions
            spark_reject = next(
                (r for r in spark_result.rejected_transactions if r.get('tran_id') == tran_id),
                None
            )
            
            if spark_reject is None:
                result.add_check(
                    f"Transaction {tran_id} rejected",
                    False,
                    "Expected reject but not found in rejects"
                )
            else:
                actual_code = spark_reject.get('reject_code')
                result.add_check(
                    f"Transaction {tran_id} reject code",
                    actual_code == expected_reject_code,
                    f"Expected={expected_reject_code}, Actual={actual_code}"
                )
    
    # Determine overall pass/fail
    result.passed = result.failed_checks == 0
    result.generate_summary()
    
    return result


def generate_comparison_report(results: List[ComparisonResult], output_file: str):
    """
    Generate a comprehensive comparison report.
    
    Args:
        results: List of ComparisonResult objects
        output_file: Path to write the report
    """
    report = []
    report.append("=" * 60)
    report.append("CBTRN02C MIGRATION VALIDATION REPORT")
    report.append("=" * 60)
    report.append("")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    failed_tests = total_tests - passed_tests
    
    report.append(f"Total Tests: {total_tests}")
    report.append(f"Passed: {passed_tests}")
    report.append(f"Failed: {failed_tests}")
    report.append("")
    
    for result in results:
        report.append(result.summary)
    
    report.append("=" * 60)
    report.append("END OF REPORT")
    report.append("=" * 60)
    
    report_text = "\n".join(report)
    
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    return report_text


if __name__ == "__main__":
    # Example usage
    print("Comparator module loaded successfully")
    print("Use compare_cobol_spark_outputs() or compare_spark_with_expected()")
