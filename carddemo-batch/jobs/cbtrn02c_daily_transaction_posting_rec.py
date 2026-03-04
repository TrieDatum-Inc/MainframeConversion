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
    spark-submit cbtrn02c_job.py [--catalog SPARK_CATALOG] [--database DATABASE]

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
    IntegerType, TimestampType, LongType, DoubleType
)
sys.path.insert(0, "..")
from utils.spark_utils import get_spark_session, get_db_prefix
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
        database: str
    ):
        self.spark = spark
        self.database = database

        # Table names (Databricks CE uses database.table format)
        self.dalytran_table = f"{database}.daily_transaction"
        self.transactions_table = f"{database}.transactions"
        self.accounts_table = f"{database}.account"
        self.card_xref_table = f"{database}.card_xref"
        self.tran_cat_balance_table = f"{database}.tran_cat_bal"
        self.rejects_table = f"{database}.daily_reject"

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
        print(f"Database: {self.database}")
        print("=" * 60)

        # Step 1: Read daily transactions
        dalytran_df = self._read_daily_transactions()
        self.records_read = dalytran_df.count()
        print(f"Records read from DAILY_TRANSACTION: {self.records_read}")

        if self.records_read == 0:
            print("No transactions to process. Exiting.")
            return self._generate_stats()

        # Step 2: Process transactions sequentially by account
        # This matches COBOL behavior where balance updates affect subsequent validations
        valid_df, rejects_df, valid_count, reject_count = self._process_transactions_sequentially(dalytran_df)

        # IMPORTANT: Collect reject data BEFORE posting transactions
        # because _post_transactions modifies the accounts table, which can
        # affect the rejects_df when it's re-evaluated
        reject_data = None
        if reject_count > 0:
            reject_data = rejects_df.select(
                "tran_id", "tran_type_cd","tran_cat_cd", "tran_source", "tran_desc", "tran_amt",
                "merchant_id", "merchant_name", "merchant_city", "merchant_zip",
                "card_num","orig_ts", "proc_ts", "reject_reason_cd"
            ).collect()

        # Step 3: Post valid transactions
        if valid_count > 0:
            self._post_transactions(valid_df)
            self.records_written = valid_count

        # Step 4: Write rejects (using pre-collected data)
        if reject_count > 0 and reject_data:
            self._write_rejects_from_data(reject_data)
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
        """Read daily transactions from DAILY_TRANSACTION table.
        """
        query = f"""
            SELECT * FROM {self.dalytran_table}
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
        # COBOL formula: WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
        # COBOL check: IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL
        #
        # With our sign convention (purchases are negative, payments are positive):
        # - projected_balance becomes negative when in debt
        # - We need to check if the debt exceeds the credit limit
        # - Pass if projected_balance >= -credit_limit (i.e., debt doesn't exceed limit)
        #
        # Examples:
        # - credit_limit=1000, projected_balance=-1000 → -1000 >= -1000 → TRUE (pass, exactly at limit)
        # - credit_limit=1000, projected_balance=-1050 → -1050 >= -1000 → FALSE (reject, overlimit)
        # - credit_limit=1000, projected_balance=500 → 500 >= -1000 → TRUE (pass, payment/credit)
        joined_df = joined_df.withColumn(
            "v3_within_limit",
            F.col("projected_balance") >= -F.col("credit_limit")
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
            "reject_reason_cd",
            F.coalesce(
                F.col("reject_code_1"),
                F.col("reject_code_2"),
                F.col("reject_code_3"),
                F.col("reject_code_4")
            )
        )

        # Split into valid and rejected
        # Cache the joined_df to ensure consistent results when filtering
        # joined_df = joined_df.cache()
        joined_df.count()  # Force materialization

        valid_df = joined_df.filter(F.col("is_valid") == True)
        rejects_df = joined_df.filter(F.col("is_valid") == False)

        # Cache the results to ensure they're not re-evaluated
        # valid_df = valid_df.cache()
        # rejects_df = rejects_df.cache()

        # Force materialization and get counts
        # IMPORTANT: We return the counts here because calling count() again later
        # after _post_transactions updates the accounts table can cause issues
        valid_count = valid_df.count()
        reject_count = rejects_df.count()

        return valid_df, rejects_df, valid_count, reject_count

    def _post_transactions(self, valid_df: DataFrame):
        """Post valid transactions to TRANSACTIONS table and update balances.

        IDEMPOTENCY: Uses MERGE keyed by (tran_id) to prevent duplicates.
        Only applies balance updates for transactions not already posted.
        
        NOTE: Uses collect/recreate pattern instead of persist/cache for compatibility
        with Databricks Community Edition (Spark Connect).
        """
        from delta.tables import DeltaTable
        from pyspark.sql.types import StructType, StructField, StringType, DecimalType, TimestampType
        from decimal import Decimal as PyDecimal

        proc_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")[:26]

        # Prepare transaction records
        tran_records = valid_df.select(
            "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
            "tran_amt", "merchant_id", "merchant_name", "merchant_city",
            "merchant_zip", "card_num", "orig_ts", "xref_acct_id"
        ).withColumn("proc_ts", F.lit(proc_ts)) \
         .withColumn("created_ts", F.current_timestamp())

        # IDEMPOTENCY: Find transactions already posted 
        existing_posted = (
            self.spark.table(self.transactions_table)
            .select("tran_id").distinct()
        )

        # Filter to only NEW transactions (not already posted)
        new_tran_records = tran_records.join(existing_posted, on="tran_id", how="left_anti")
        
        # IMPORTANT: Compute balance update aggregates BEFORE the MERGE
        # This avoids Spark lazy evaluation issues where the DataFrame would be
        # re-evaluated after MERGE modifies the table (causing empty results)
        # We use collect/recreate pattern instead of persist/cache for Databricks CE compatibility
        
        # Compute account balance updates and materialize via collect
        account_updates_rows = new_tran_records.groupBy("xref_acct_id").agg(
            F.sum("tran_amt").alias("total_amt"),
            F.sum(F.when(F.col("tran_amt") >= 0, F.col("tran_amt")).otherwise(0)).alias("credit_amt"),
            F.sum(F.when(F.col("tran_amt") < 0, F.col("tran_amt")).otherwise(0)).alias("debit_amt")
        ).collect()
        
        # Compute category balance updates and materialize via collect
        cat_updates_rows = new_tran_records.groupBy(
            "xref_acct_id", "tran_type_cd", "tran_cat_cd"
        ).agg(
            F.sum("tran_amt").alias("total_amt")
        ).collect()
        
        # Get count and check if empty
        new_count = len(account_updates_rows) if account_updates_rows else 0
        # Also need to get actual transaction count for insert
        insert_records = new_tran_records.select(
            "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
            "tran_amt", "merchant_id", "merchant_name", "merchant_city",
            "merchant_zip", "card_num", "orig_ts", "proc_ts"
        )
        insert_rows = insert_records.collect()
        tran_count = len(insert_rows)

        if tran_count == 0:
            print(f"All transactions already posted. Skipping.")
            return

        # Recreate insert_records DataFrame from collected rows
        insert_records_mat = self.spark.createDataFrame(insert_rows, insert_records.schema)

        # Use MERGE to insert new transactions (tran_id)
        tx_delta = DeltaTable.forName(self.spark, self.transactions_table)

        tx_delta.alias("t").merge(
            insert_records_mat.alias("s"),
            "t.tran_id = s.tran_id"
        ).whenNotMatchedInsertAll().execute()

        print(f"Posted {tran_count} NEW transactions to {self.transactions_table}")

        # IDEMPOTENCY: Apply balance updates using materialized aggregates
        # These were computed BEFORE the MERGE, so they reflect the correct "new" transactions
        if account_updates_rows:
            self._update_account_balances_from_rows(account_updates_rows)

        if cat_updates_rows:
            self._update_tran_cat_balances_from_rows(cat_updates_rows)
    
    def _update_account_balances_from_rows(self, account_updates_rows: list):
        """
        Update account balances from pre-collected aggregated rows.
        
        This method accepts pre-materialized data to avoid Spark lazy evaluation
        issues when the source table has been modified.
        """
        from delta.tables import DeltaTable
        from pyspark.sql.types import StructType, StructField, StringType, DecimalType
        
        # Define schema for account updates
        schema = StructType([
            StructField("xref_acct_id", StringType(), True),
            StructField("total_amt", DecimalType(11, 2), True),
            StructField("credit_amt", DecimalType(11, 2), True),
            StructField("debit_amt", DecimalType(11, 2), True)
        ])
        
        # Recreate DataFrame from collected rows
        account_updates = self.spark.createDataFrame(account_updates_rows, schema)
        
        accounts_delta = DeltaTable.forName(self.spark, self.accounts_table)

        accounts_delta.alias("a").merge(
            account_updates.alias("u"),
            "a.acct_id = u.xref_acct_id"
        ).whenMatchedUpdate(set={
            "curr_bal": F.col("a.curr_bal") + F.col("u.total_amt"),
            "curr_cyc_credit": F.col("a.curr_cyc_credit") + F.col("u.credit_amt"),
            "curr_cyc_debit": F.col("a.curr_cyc_debit") + F.col("u.debit_amt")
        }).execute()

        print(f"Updated {len(account_updates_rows)} account balances")
    
    def _update_tran_cat_balances_from_rows(self, cat_updates_rows: list):
        """
        Update transaction category balances from pre-collected aggregated rows.
        
        This method accepts pre-materialized data to avoid Spark lazy evaluation
        issues when the source table has been modified.
        """
        from delta.tables import DeltaTable
        from pyspark.sql.types import StructType, StructField, StringType, DecimalType
        
        # Define schema for category updates
        schema = StructType([
            StructField("xref_acct_id", StringType(), True),
            StructField("tran_type_cd", StringType(), True),
            StructField("tran_cat_cd", StringType(), True),
            StructField("total_amt", DecimalType(11, 2), True)
        ])
        
        # Recreate DataFrame from collected rows
        cat_updates = self.spark.createDataFrame(cat_updates_rows, schema)
        cat_updates = cat_updates.withColumnRenamed("xref_acct_id", "acct_id")

        try:
            tran_cat_delta = DeltaTable.forName(self.spark, self.tran_cat_balance_table)

            tran_cat_delta.alias("t").merge(
                cat_updates.alias("u"),
                """t.acct_id = u.acct_id
                   AND t.tran_type_cd = u.tran_type_cd
                   AND t.tran_cat_cd = u.tran_cat_cd"""
            ).whenMatchedUpdate(set={
                "tran_cat_bal": F.col("t.tran_cat_bal") + F.col("u.total_amt")
            }).whenNotMatchedInsert(values={
                "acct_id": F.col("u.acct_id"),
                "tran_type_cd": F.col("u.tran_type_cd"),
                "tran_cat_cd": F.col("u.tran_cat_cd"),
                "tran_cat_bal": F.col("u.total_amt")
            }).execute()

            print(f"Updated {len(cat_updates_rows)} transaction category balances")
        except Exception as e:
            print(f"Warning: Could not update tran_cat_balance: {e}")

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
            "curr_cyc_debit": F.col("a.curr_cyc_debit") + F.col("u.debit_amt")
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
                "tran_cat_bal": F.col("t.tran_cat_bal") + F.col("u.total_amt")
            }).whenNotMatchedInsert(values={
                "acct_id": F.col("u.acct_id"),
                "tran_type_cd": F.col("u.tran_type_cd"),
                "tran_cat_cd": F.col("u.tran_cat_cd"),
                "tran_cat_bal": F.col("u.total_amt")
            }).execute()

            print(f"Updated {cat_updates.count()} transaction category balances")
        except Exception as e:
            print(f"Warning: Could not update tran_cat_balance: {e}")

    def _write_rejects_from_data(self, reject_data: list):
        """
        Write rejected transactions to TRANSACTION_REJECTS table from collected data.

        IDEMPOTENCY: Uses MERGE keyed by (tran_id) to prevent duplicates.
        This method takes pre-collected data (list of Row objects) to avoid
        re-evaluation issues when the underlying tables have been modified.
        """
        from pyspark.sql.types import StructType, StructField, StringType, DecimalType, IntegerType, TimestampType
        from decimal import Decimal as PyDecimal
        from delta.tables import DeltaTable

        # Define schema to match the table schema
        schema = StructType([
            StructField("tran_id", StringType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_source", StringType()),
            StructField("tran_desc", StringType()),
            StructField("tran_amt", DecimalType(11,2)),
            StructField("merchant_id", LongType()),
            StructField("merchant_name", StringType()),
            StructField("merchant_city", StringType()),
            StructField("merchant_zip", StringType()),
            StructField("card_num", StringType()),
            StructField("orig_ts", StringType()),
            StructField("proc_ts", StringType()),
            StructField("reject_reason_cd", IntegerType()),
            StructField("reject_reason_desc", StringType())
        ])

        # Convert collected data to list of tuples with proper types
        reject_rows = []
        for row in reject_data:
            reject_code = row.reject_reason_cd
            # Convert tran_amt to Python Decimal with proper precision
            tran_amt = PyDecimal(str(row.tran_amt)) if row.tran_amt is not None else None
            reject_rows.append((
                row.tran_id,
                row.tran_type_cd,
                row.tran_cat_cd,
                row.tran_source,
                row.tran_desc,
                tran_amt,
                row.merchant_id,
                row.merchant_name,
                row.merchant_city,
                row.merchant_zip,
                row.card_num,
                row.orig_ts,
                row.proc_ts,
                reject_code,
                REASON_DESCRIPTIONS.get(reject_code, "UNKNOWN REASON")
            ))

        # Create DataFrame with explicit schema
        reject_df = self.spark.createDataFrame(reject_rows, schema)

        # IDEMPOTENCY: Find rejects already written for this
        existing_rejects = (
            self.spark.table(self.rejects_table)
            .select("tran_id").distinct()
        )

        # Filter to only NEW rejects (not already written)
        new_reject_df = reject_df.join(existing_rejects, on="tran_id", how="left_anti")
        new_count = new_reject_df.count()

        if new_count == 0:
            print(f"All rejects already written. Skipping.")
            return

        # Use MERGE to insert new rejects (keyed by tran_id)
        rej_delta = DeltaTable.forName(self.spark, self.rejects_table)

        rej_delta.alias("t").merge(
            new_reject_df.alias("s"),
            "t.tran_id = s.tran_id"
        ).whenNotMatchedInsertAll().execute()

        print(f"Wrote {new_count} NEW rejects to {self.rejects_table}")

    def _generate_stats(self) -> dict:
        """Generate reconciliation statistics."""
        return {
            "records_read": self.records_read,
            "records_written": self.records_written,
            "records_rejected": self.records_rejected,
            "timestamp": datetime.now().isoformat()
        }


def main():
    spark = get_spark_session("CBTRN02C_DailyTransactionPosting")

    # Run the job
    job = CBTRN02CJob(
        spark=spark,
        database="carddemo"
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
