#!/usr/bin/env python3
"""
CBTRN02C - Post Daily Transactions - PySpark Job for Databricks Community Edition

This script replicates the mainframe COBOL batch program CBTRN02C which:
1. Reads daily transactions from the DALYTRAN table
2. Validates each transaction against business rules
3. Posts valid transactions to the TRANSACTIONS table
4. Updates account balances in the ACCOUNTS table
5. Updates transaction category balances in TRAN_CAT_BALANCE table
6. Writes rejected transactions to TRANSACTION_REJECTS table

Usage:
    spark-submit cbtrn02c_job.py [--batch-id BATCH_ID] [--database DATABASE]

For Databricks Community Edition:
    - Run from a notebook: %run /path/to/cbtrn02c_job
    - Or upload and run via Databricks CLI

Author: Migrated from COBOL CBTRN02C
"""

import argparse
import sys
from datetime import datetime
from decimal import Decimal
from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType, 
    IntegerType, TimestampType, LongType
)

# Validation reason codes (matching COBOL CBTRN02C exactly)
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


class CBTRN02CJob:
    """
    PySpark implementation of CBTRN02C batch job.
    
    This class processes daily transactions sequentially (like COBOL) to ensure
    proper balance updates when multiple transactions affect the same account.
    """
    
    def __init__(
        self,
        spark: SparkSession,
        database: str = "carddemo",
        batch_id: str = None
    ):
        self.spark = spark
        self.database = database
        self.batch_id = batch_id or datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Table names (Databricks CE uses database.table format)
        self.dalytran_table = f"{database}.dalytran"
        self.transactions_table = f"{database}.transactions"
        self.accounts_table = f"{database}.accounts"
        self.card_xref_table = f"{database}.card_xref"
        self.tran_cat_balance_table = f"{database}.tran_cat_balance"
        self.rejects_table = f"{database}.transaction_rejects"
        
        # Counters for reconciliation
        self.records_read = 0
        self.records_written = 0
        self.records_rejected = 0
        
    def run(self) -> dict:
        """
        Main entry point - runs the complete CBTRN02C job.
        
        Returns:
            dict: Statistics including records read, written, rejected
        """
        print("=" * 60)
        print("CBTRN02C - POST DAILY TRANSACTIONS - STARTING")
        print(f"Batch ID: {self.batch_id}")
        print(f"Database: {self.database}")
        print("=" * 60)
        
        # Step 1: Read daily transactions
        dalytran_df = self._read_daily_transactions()
        self.records_read = dalytran_df.count()
        print(f"Records read from DALYTRAN: {self.records_read}")
        
        if self.records_read == 0:
            print("No transactions to process. Exiting.")
            return self._generate_stats()
        
        # Step 2: Process transactions sequentially by account
        # This matches COBOL behavior where balance updates affect subsequent validations
        valid_df, rejects_df = self._process_transactions_sequentially(dalytran_df)
        
        # Step 3: Post valid transactions
        valid_count = valid_df.count() if valid_df else 0
        if valid_count > 0:
            self._post_transactions(valid_df)
            self.records_written = valid_count
        
        # Step 4: Write rejects
        reject_count = rejects_df.count() if rejects_df else 0
        if reject_count > 0:
            self._write_rejects(rejects_df)
            self.records_rejected = reject_count
        
        # Step 5: Generate reconciliation report
        stats = self._generate_stats()
        
        print("=" * 60)
        print("CBTRN02C - POST DAILY TRANSACTIONS - COMPLETED")
        print(f"Transactions Processed: {self.records_read}")
        print(f"Transactions Posted:    {self.records_written}")
        print(f"Transactions Rejected:  {self.records_rejected}")
        print("=" * 60)
        
        return stats
    
    def _read_daily_transactions(self) -> DataFrame:
        """Read daily transactions from DALYTRAN table."""
        query = f"""
            SELECT * FROM {self.dalytran_table}
            WHERE batch_id = '{self.batch_id}'
            OR batch_id IS NULL
            ORDER BY tran_id
        """
        return self.spark.sql(query)
    
    def _process_transactions_sequentially(self, dalytran_df: DataFrame):
        """
        Process transactions sequentially to match COBOL behavior.
        
        COBOL processes one transaction at a time, updating account balances
        after each transaction. This affects overlimit validation for subsequent
        transactions on the same account.
        
        We implement this using window functions with running totals.
        """
        # Load reference data
        xref_df = self.spark.table(self.card_xref_table)
        accounts_df = self.spark.table(self.accounts_table)
        
        # Join with card_xref to get account ID
        joined_df = dalytran_df.alias("t").join(
            xref_df.alias("x"),
            F.col("t.card_num") == F.col("x.card_num"),
            "left"
        ).select(
            "t.*",
            F.col("x.acct_id").alias("xref_acct_id"),
            F.col("x.cust_id").alias("xref_cust_id")
        )
        
        # Validation 1: Card number exists in XREFFILE
        joined_df = joined_df.withColumn(
            "v1_card_valid",
            F.col("xref_acct_id").isNotNull()
        ).withColumn(
            "reject_code_1",
            F.when(~F.col("v1_card_valid"), F.lit(REASON_INVALID_CARD))
        )
        
        # Join with accounts to get account details
        joined_df = joined_df.alias("t").join(
            accounts_df.alias("a"),
            F.col("t.xref_acct_id") == F.col("a.acct_id"),
            "left"
        ).select(
            "t.*",
            F.col("a.acct_id").alias("account_acct_id"),
            F.col("a.active_status"),
            F.col("a.curr_bal"),
            F.col("a.credit_limit"),
            F.col("a.expiration_date"),
            F.col("a.curr_cyc_credit"),
            F.col("a.curr_cyc_debit")
        )
        
        # Validation 2: Account exists in ACCTFILE
        joined_df = joined_df.withColumn(
            "v2_account_exists",
            F.col("account_acct_id").isNotNull()
        ).withColumn(
            "reject_code_2",
            F.when(
                F.col("v1_card_valid") & ~F.col("v2_account_exists"),
                F.lit(REASON_ACCOUNT_NOT_FOUND)
            )
        )
        
        # Calculate running balance per account for sequential processing
        # This is the key to matching COBOL behavior
        window_spec = Window.partitionBy("xref_acct_id").orderBy("tran_id").rowsBetween(
            Window.unboundedPreceding, Window.currentRow
        )
        
        # Running sum of transaction amounts for this account
        joined_df = joined_df.withColumn(
            "running_tran_sum",
            F.sum("tran_amt").over(window_spec)
        )
        
        # Calculate projected balance after this transaction
        # COBOL formula: WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
        # With sequential processing, we need running total
        joined_df = joined_df.withColumn(
            "projected_balance",
            F.col("curr_cyc_credit") - F.col("curr_cyc_debit") + F.col("running_tran_sum")
        )
        
        # Validation 3: Overlimit check
        # Pass if credit_limit >= projected_balance
        joined_df = joined_df.withColumn(
            "v3_within_limit",
            F.col("credit_limit") >= F.col("projected_balance")
        ).withColumn(
            "reject_code_3",
            F.when(
                F.col("v1_card_valid") & 
                F.col("v2_account_exists") & 
                ~F.col("v3_within_limit"),
                F.lit(REASON_OVERLIMIT)
            )
        )
        
        # Validation 4: Expiration check
        # Extract date from timestamp (first 10 chars: YYYY-MM-DD)
        joined_df = joined_df.withColumn(
            "tran_date",
            F.substring(F.col("orig_ts"), 1, 10)
        ).withColumn(
            "v4_not_expired",
            F.col("expiration_date") >= F.col("tran_date")
        ).withColumn(
            "reject_code_4",
            F.when(
                F.col("v1_card_valid") & 
                F.col("v2_account_exists") & 
                F.col("v3_within_limit") & 
                ~F.col("v4_not_expired"),
                F.lit(REASON_EXPIRED)
            )
        )
        
        # Determine final validation status
        joined_df = joined_df.withColumn(
            "is_valid",
            F.col("v1_card_valid") & 
            F.col("v2_account_exists") & 
            F.col("v3_within_limit") & 
            F.col("v4_not_expired")
        ).withColumn(
            "reject_reason_code",
            F.coalesce(
                F.col("reject_code_1"),
                F.col("reject_code_2"),
                F.col("reject_code_3"),
                F.col("reject_code_4")
            )
        )
        
        # Split into valid and rejected
        valid_df = joined_df.filter(F.col("is_valid") == True)
        rejects_df = joined_df.filter(F.col("is_valid") == False)
        
        return valid_df, rejects_df
    
    def _post_transactions(self, valid_df: DataFrame):
        """Post valid transactions to TRANSACTIONS table and update balances."""
        proc_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")[:26]
        
        # Prepare transaction records
        tran_records = valid_df.select(
            "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
            "tran_amt", "merchant_id", "merchant_name", "merchant_city",
            "merchant_zip", "card_num", "orig_ts"
        ).withColumn("proc_ts", F.lit(proc_ts)) \
         .withColumn("batch_id", F.lit(self.batch_id)) \
         .withColumn("created_ts", F.current_timestamp())
        
        # Write to transactions table
        tran_records.write.format("delta").mode("append").saveAsTable(self.transactions_table)
        print(f"Posted {tran_records.count()} transactions to {self.transactions_table}")
        
        # Update account balances
        self._update_account_balances(valid_df)
        
        # Update transaction category balances
        self._update_tran_cat_balances(valid_df)
    
    def _update_account_balances(self, valid_df: DataFrame):
        """
        Update account balances after posting transactions.
        
        COBOL logic:
        - ADD DALYTRAN-AMT TO ACCT-CURR-BAL
        - IF DALYTRAN-AMT >= 0: ADD TO ACCT-CURR-CYC-CREDIT
        - ELSE: ADD TO ACCT-CURR-CYC-DEBIT
        """
        # Aggregate transaction amounts by account
        account_updates = valid_df.groupBy("xref_acct_id").agg(
            F.sum("tran_amt").alias("total_amt"),
            F.sum(F.when(F.col("tran_amt") >= 0, F.col("tran_amt")).otherwise(0)).alias("credit_amt"),
            F.sum(F.when(F.col("tran_amt") < 0, F.col("tran_amt")).otherwise(0)).alias("debit_amt")
        )
        
        # Use MERGE to update accounts
        from delta.tables import DeltaTable
        
        accounts_delta = DeltaTable.forName(self.spark, self.accounts_table)
        
        accounts_delta.alias("a").merge(
            account_updates.alias("u"),
            "a.acct_id = u.xref_acct_id"
        ).whenMatchedUpdate(set={
            "curr_bal": F.col("a.curr_bal") + F.col("u.total_amt"),
            "curr_cyc_credit": F.col("a.curr_cyc_credit") + F.col("u.credit_amt"),
            "curr_cyc_debit": F.col("a.curr_cyc_debit") + F.col("u.debit_amt"),
            "last_updated_ts": F.current_timestamp(),
            "last_updated_batch_id": F.lit(self.batch_id)
        }).execute()
        
        print(f"Updated {account_updates.count()} account balances")
    
    def _update_tran_cat_balances(self, valid_df: DataFrame):
        """
        Update transaction category balances.
        
        COBOL logic:
        - Key: ACCT-ID + TYPE-CD + CAT-CD
        - If record exists: ADD DALYTRAN-AMT TO TRAN-CAT-BAL
        - If not exists: Create new record with TRAN-CAT-BAL = DALYTRAN-AMT
        """
        # Aggregate by account + type + category
        cat_updates = valid_df.groupBy(
            "xref_acct_id", "tran_type_cd", "tran_cat_cd"
        ).agg(
            F.sum("tran_amt").alias("total_amt")
        ).withColumnRenamed("xref_acct_id", "acct_id")
        
        # Use MERGE for upsert
        from delta.tables import DeltaTable
        
        try:
            tran_cat_delta = DeltaTable.forName(self.spark, self.tran_cat_balance_table)
            
            tran_cat_delta.alias("t").merge(
                cat_updates.alias("u"),
                """t.acct_id = u.acct_id 
                   AND t.tran_type_cd = u.tran_type_cd 
                   AND t.tran_cat_cd = u.tran_cat_cd"""
            ).whenMatchedUpdate(set={
                "tran_cat_bal": F.col("t.tran_cat_bal") + F.col("u.total_amt"),
                "last_updated_ts": F.current_timestamp(),
                "last_updated_batch_id": F.lit(self.batch_id)
            }).whenNotMatchedInsert(values={
                "acct_id": F.col("u.acct_id"),
                "tran_type_cd": F.col("u.tran_type_cd"),
                "tran_cat_cd": F.col("u.tran_cat_cd"),
                "tran_cat_bal": F.col("u.total_amt"),
                "last_updated_ts": F.current_timestamp(),
                "last_updated_batch_id": F.lit(self.batch_id)
            }).execute()
            
            print(f"Updated {cat_updates.count()} transaction category balances")
        except Exception as e:
            print(f"Warning: Could not update tran_cat_balance: {e}")
    
    def _write_rejects(self, rejects_df: DataFrame):
        """Write rejected transactions to TRANSACTION_REJECTS table."""
        reject_records = rejects_df.select(
            "tran_id", "card_num", "tran_amt", "orig_ts", "reject_reason_code"
        ).withColumn(
            "reject_reason_desc",
            F.when(F.col("reject_reason_code") == 100, F.lit(REASON_DESCRIPTIONS[100]))
             .when(F.col("reject_reason_code") == 101, F.lit(REASON_DESCRIPTIONS[101]))
             .when(F.col("reject_reason_code") == 102, F.lit(REASON_DESCRIPTIONS[102]))
             .when(F.col("reject_reason_code") == 103, F.lit(REASON_DESCRIPTIONS[103]))
             .otherwise(F.lit("UNKNOWN REJECTION REASON"))
        ).withColumn("batch_id", F.lit(self.batch_id)) \
         .withColumn("rejected_ts", F.current_timestamp())
        
        reject_records.write.format("delta").mode("append").saveAsTable(self.rejects_table)
        print(f"Wrote {reject_records.count()} rejects to {self.rejects_table}")
    
    def _generate_stats(self) -> dict:
        """Generate reconciliation statistics."""
        return {
            "batch_id": self.batch_id,
            "records_read": self.records_read,
            "records_written": self.records_written,
            "records_rejected": self.records_rejected,
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main entry point for spark-submit."""
    parser = argparse.ArgumentParser(
        description="CBTRN02C - Post Daily Transactions to Databricks"
    )
    parser.add_argument(
        "--batch-id", "-b",
        help="Batch ID for this run (default: current timestamp)",
        default=None
    )
    parser.add_argument(
        "--database", "-d",
        help="Database name (default: carddemo)",
        default="carddemo"
    )
    
    args = parser.parse_args()
    
    # Create or get Spark session
    spark = SparkSession.builder \
        .appName("CBTRN02C_PostDailyTransactions") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()
    
    # Set database
    spark.sql(f"USE {args.database}")
    
    # Run the job
    job = CBTRN02CJob(
        spark=spark,
        database=args.database,
        batch_id=args.batch_id
    )
    
    stats = job.run()
    
    # Print final stats as JSON for shell script parsing
    import json
    print("\n--- JOB STATS ---")
    print(json.dumps(stats, indent=2))
    
    # Return code based on rejects
    if stats["records_rejected"] > 0:
        sys.exit(4)  # Warning: some rejects (matches COBOL return code)
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()
