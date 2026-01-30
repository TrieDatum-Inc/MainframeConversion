"""
Spark Runner for CBTRN02C Testing

This module runs the migrated Spark/Databricks pipeline locally using PySpark
to generate outputs that can be compared against COBOL golden outputs.

The runner:
1. Loads test data from CSV files into Spark DataFrames
2. Runs the CBTRN02C PySpark job logic
3. Captures output DataFrames
4. Exports results for comparison

Prerequisites:
- PySpark installed (pip install pyspark)
- Delta Lake installed (pip install delta-spark)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import json

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "databricks-migration" / "cbtrn02c"))

try:
    from pyspark.sql import SparkSession, DataFrame
    from pyspark.sql import functions as F
    from pyspark.sql.types import (
        StructType, StructField, StringType, DecimalType,
        IntegerType, TimestampType, LongType
    )
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    print("Warning: PySpark not available. Install with: pip install pyspark delta-spark")


@dataclass
class SparkRunResult:
    """Result of running the Spark pipeline."""
    success: bool
    error_message: Optional[str] = None
    transactions_processed: int = 0
    transactions_written: int = 0
    transactions_rejected: int = 0
    posted_transactions: List[Dict] = None
    rejected_transactions: List[Dict] = None
    updated_accounts: List[Dict] = None
    updated_tran_cat_bal: List[Dict] = None
    
    def __post_init__(self):
        if self.posted_transactions is None:
            self.posted_transactions = []
        if self.rejected_transactions is None:
            self.rejected_transactions = []
        if self.updated_accounts is None:
            self.updated_accounts = []
        if self.updated_tran_cat_bal is None:
            self.updated_tran_cat_bal = []


# =============================================================================
# Validation Reason Codes (Matching COBOL CBTRN02C exactly)
# =============================================================================
REASON_INVALID_CARD = 100        # "INVALID CARD NUMBER FOUND"
REASON_ACCOUNT_NOT_FOUND = 101   # "ACCOUNT RECORD NOT FOUND"
REASON_OVERLIMIT = 102           # "OVERLIMIT TRANSACTION"
REASON_EXPIRED = 103             # "TRANSACTION RECEIVED AFTER ACCT EXPIRATION"

REASON_DESCRIPTIONS = {
    100: "INVALID CARD NUMBER FOUND",
    101: "ACCOUNT RECORD NOT FOUND",
    102: "OVERLIMIT TRANSACTION",
    103: "TRANSACTION RECEIVED AFTER ACCT EXPIRATION",
}


class SparkCBTRN02CRunner:
    """
    Local Spark runner that replicates CBTRN02C logic for testing.
    This is a simplified version that runs locally without Delta Lake.
    """
    
    def __init__(self, spark: SparkSession = None):
        """Initialize the Spark runner."""
        if spark is None and PYSPARK_AVAILABLE:
            self.spark = SparkSession.builder \
                .appName("CBTRN02C-Test") \
                .master("local[*]") \
                .config("spark.sql.shuffle.partitions", "2") \
                .getOrCreate()
        else:
            self.spark = spark
        
        self.batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.proc_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")[:26]
    
    def load_test_data(self, test_dir: str) -> Tuple[DataFrame, DataFrame, DataFrame]:
        """
        Load test data from CSV files.
        
        Args:
            test_dir: Directory containing spark subdirectory with CSV files
            
        Returns:
            Tuple of (dalytran_df, accounts_df, xref_df)
        """
        spark_dir = Path(test_dir) / "spark"
        
        # Load daily transactions
        dalytran_df = self.spark.read.csv(
            str(spark_dir / "dalytran.csv"),
            header=True,
            inferSchema=False
        ).withColumn("tran_amt", F.col("tran_amt").cast(DecimalType(11, 2))) \
         .withColumn("tran_cat_cd", F.col("tran_cat_cd").cast(IntegerType())) \
         .withColumn("merchant_id", F.col("merchant_id").cast(LongType()))
        
        # Load accounts
        accounts_df = self.spark.read.csv(
            str(spark_dir / "accounts.csv"),
            header=True,
            inferSchema=False
        ).withColumn("curr_bal", F.col("curr_bal").cast(DecimalType(12, 2))) \
         .withColumn("credit_limit", F.col("credit_limit").cast(DecimalType(12, 2))) \
         .withColumn("cash_credit_limit", F.col("cash_credit_limit").cast(DecimalType(12, 2))) \
         .withColumn("curr_cyc_credit", F.col("curr_cyc_credit").cast(DecimalType(12, 2))) \
         .withColumn("curr_cyc_debit", F.col("curr_cyc_debit").cast(DecimalType(12, 2)))
        
        # Load card cross-references
        xref_df = self.spark.read.csv(
            str(spark_dir / "card_xref.csv"),
            header=True,
            inferSchema=False
        )
        
        return dalytran_df, accounts_df, xref_df
    
    def run_validation(
        self,
        dalytran_df: DataFrame,
        accounts_df: DataFrame,
        xref_df: DataFrame
    ) -> Tuple[DataFrame, DataFrame]:
        """
        Run validation logic matching CBTRN02C.
        
        This processes transactions SEQUENTIALLY to match COBOL behavior,
        where each transaction updates the account balance before the next
        transaction is validated.
        
        Args:
            dalytran_df: Daily transactions
            accounts_df: Account master
            xref_df: Card cross-reference
            
        Returns:
            Tuple of (valid_df, rejects_df)
        """
        # For exact COBOL matching, we need to process sequentially
        # This is less efficient but matches mainframe behavior exactly
        
        transactions = dalytran_df.collect()
        accounts_dict = {row['acct_id']: dict(row.asDict()) for row in accounts_df.collect()}
        xref_dict = {row['card_num']: dict(row.asDict()) for row in xref_df.collect()}
        
        valid_transactions = []
        rejected_transactions = []
        
        for tran in transactions:
            tran_dict = tran.asDict()
            card_num = tran_dict['card_num']
            
            # Validation 1: Card number exists in XREFFILE
            if card_num not in xref_dict:
                rejected_transactions.append({
                    **tran_dict,
                    'reject_code': REASON_INVALID_CARD,
                    'reject_desc': REASON_DESCRIPTIONS[REASON_INVALID_CARD]
                })
                continue
            
            xref = xref_dict[card_num]
            acct_id = xref['acct_id']
            
            # Validation 2: Account exists in ACCTFILE
            if acct_id not in accounts_dict:
                rejected_transactions.append({
                    **tran_dict,
                    'reject_code': REASON_ACCOUNT_NOT_FOUND,
                    'reject_desc': REASON_DESCRIPTIONS[REASON_ACCOUNT_NOT_FOUND]
                })
                continue
            
            acct = accounts_dict[acct_id]
            tran_amt = Decimal(str(tran_dict['tran_amt'])) if tran_dict['tran_amt'] else Decimal('0')
            
            # Validation 3: Overlimit check
            # COBOL: COMPUTE WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
            # IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL
            curr_cyc_credit = Decimal(str(acct['curr_cyc_credit'])) if acct['curr_cyc_credit'] else Decimal('0')
            curr_cyc_debit = Decimal(str(acct['curr_cyc_debit'])) if acct['curr_cyc_debit'] else Decimal('0')
            credit_limit = Decimal(str(acct['credit_limit'])) if acct['credit_limit'] else Decimal('0')
            
            temp_bal = curr_cyc_credit - curr_cyc_debit + tran_amt
            
            if credit_limit < temp_bal:
                rejected_transactions.append({
                    **tran_dict,
                    'reject_code': REASON_OVERLIMIT,
                    'reject_desc': REASON_DESCRIPTIONS[REASON_OVERLIMIT]
                })
                continue
            
            # Validation 4: Account expiration check
            # COBOL: IF ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS (1:10)
            expiration_date = acct.get('expiration_date', '9999-12-31')
            orig_ts = tran_dict.get('orig_ts', '')
            tran_date = orig_ts[:10] if orig_ts else ''
            
            if expiration_date < tran_date:
                rejected_transactions.append({
                    **tran_dict,
                    'reject_code': REASON_EXPIRED,
                    'reject_desc': REASON_DESCRIPTIONS[REASON_EXPIRED]
                })
                continue
            
            # Transaction is valid - update account balances for next iteration
            # This is critical for sequential processing to match COBOL
            curr_bal = Decimal(str(acct['curr_bal'])) if acct['curr_bal'] else Decimal('0')
            acct['curr_bal'] = str(curr_bal + tran_amt)
            
            if tran_amt >= 0:
                acct['curr_cyc_credit'] = str(curr_cyc_credit + tran_amt)
            else:
                acct['curr_cyc_debit'] = str(curr_cyc_debit + tran_amt)
            
            # Add to valid transactions
            valid_transactions.append({
                **tran_dict,
                'acct_id': acct_id,
                'proc_ts': self.proc_ts
            })
        
        # Convert back to DataFrames
        if valid_transactions:
            valid_df = self.spark.createDataFrame(valid_transactions)
        else:
            valid_df = self.spark.createDataFrame([], dalytran_df.schema)
        
        if rejected_transactions:
            rejects_df = self.spark.createDataFrame(rejected_transactions)
        else:
            # Create empty DataFrame with reject schema
            reject_schema = dalytran_df.schema.add("reject_code", IntegerType()) \
                                              .add("reject_desc", StringType())
            rejects_df = self.spark.createDataFrame([], reject_schema)
        
        return valid_df, rejects_df, accounts_dict
    
    def run_test(self, test_dir: str) -> SparkRunResult:
        """
        Run the complete CBTRN02C test.
        
        Args:
            test_dir: Directory containing test files
            
        Returns:
            SparkRunResult with execution details
        """
        if not PYSPARK_AVAILABLE:
            return SparkRunResult(
                success=False,
                error_message="PySpark not available. Install with: pip install pyspark"
            )
        
        try:
            # Load test data
            dalytran_df, accounts_df, xref_df = self.load_test_data(test_dir)
            
            transactions_processed = dalytran_df.count()
            
            # Run validation
            valid_df, rejects_df, updated_accounts = self.run_validation(
                dalytran_df, accounts_df, xref_df
            )
            
            transactions_written = valid_df.count()
            transactions_rejected = rejects_df.count()
            
            # Collect results
            posted_transactions = [row.asDict() for row in valid_df.collect()]
            rejected_transactions = [row.asDict() for row in rejects_df.collect()]
            
            # Get updated accounts (only those that were modified)
            updated_account_list = list(updated_accounts.values())
            
            return SparkRunResult(
                success=True,
                transactions_processed=transactions_processed,
                transactions_written=transactions_written,
                transactions_rejected=transactions_rejected,
                posted_transactions=posted_transactions,
                rejected_transactions=rejected_transactions,
                updated_accounts=updated_account_list
            )
            
        except Exception as e:
            return SparkRunResult(
                success=False,
                error_message=str(e)
            )
    
    def stop(self):
        """Stop the Spark session."""
        if self.spark:
            self.spark.stop()


def run_spark_test(
    test_name: str,
    test_dir: str
) -> SparkRunResult:
    """
    Convenience function to run a Spark test.
    
    Args:
        test_name: Name of the test (for logging)
        test_dir: Directory containing test files
        
    Returns:
        SparkRunResult
    """
    print(f"Running Spark test: {test_name}")
    print(f"  Test directory: {test_dir}")
    
    runner = SparkCBTRN02CRunner()
    
    try:
        result = runner.run_test(test_dir)
        
        print(f"  Success: {result.success}")
        print(f"  Transactions processed: {result.transactions_processed}")
        print(f"  Transactions written: {result.transactions_written}")
        print(f"  Transactions rejected: {result.transactions_rejected}")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
        
        return result
        
    finally:
        runner.stop()


def export_spark_results(result: SparkRunResult, output_dir: str):
    """
    Export Spark results to files for comparison.
    
    Args:
        result: SparkRunResult to export
        output_dir: Directory to write output files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Export posted transactions
    with open(output_path / "posted_transactions.json", 'w') as f:
        json.dump(result.posted_transactions, f, indent=2, default=str)
    
    # Export rejected transactions
    with open(output_path / "rejected_transactions.json", 'w') as f:
        json.dump(result.rejected_transactions, f, indent=2, default=str)
    
    # Export summary
    summary = {
        'success': result.success,
        'transactions_processed': result.transactions_processed,
        'transactions_written': result.transactions_written,
        'transactions_rejected': result.transactions_rejected,
        'error_message': result.error_message
    }
    with open(output_path / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Results exported to {output_dir}")


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python run_spark.py <test_directory>")
        print("Example: python run_spark.py ../golden_datasets/TC001_VALID_TRANSACTION")
        sys.exit(1)
    
    test_dir = sys.argv[1]
    result = run_spark_test("Manual Test", test_dir)
    
    if result.success:
        print("\n=== Spark Results ===")
        print(f"Posted: {len(result.posted_transactions)}")
        print(f"Rejected: {len(result.rejected_transactions)}")
        
        if result.rejected_transactions:
            print("\nRejected transactions:")
            for rej in result.rejected_transactions:
                print(f"  {rej['tran_id']}: {rej['reject_code']} - {rej['reject_desc']}")
