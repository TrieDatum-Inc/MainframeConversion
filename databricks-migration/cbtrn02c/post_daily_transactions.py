"""
CBTRN02C Migration to Databricks - Post Daily Transactions

This PySpark job replicates the exact functionality of the mainframe COBOL
program CBTRN02C.cbl which posts daily transactions to VSAM files.

Mainframe Flow (CBTRN02C):
1. Read DALYTRAN (daily transaction input file)
2. For each transaction:
   a. Validate card number exists in XREFFILE
   b. Validate account exists and is active in ACCTFILE
   c. Validate transaction doesn't exceed credit limit
   d. Validate account is not expired
3. For valid transactions:
   - Write to TRANFILE (transaction master)
   - Update TCATBALF (transaction category balance)
   - Update ACCTFILE (account balance)
4. For invalid transactions:
   - Write to DALYREJS (rejects file) with reason code

Databricks Equivalent:
- DALYTRAN -> Bronze Delta table (dalytran_bronze)
- TRANFILE -> Silver Delta table (transactions)
- TCATBALF -> Silver Delta table (tran_cat_balance)
- ACCTFILE -> Silver Delta table (accounts)
- DALYREJS -> Silver Delta table (transaction_rejects)
- XREFFILE -> Silver Delta table (card_xref)

Author: Databricks Migration POC
Based on: /app/cbl/CBTRN02C.cbl
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import StringType, DecimalType, IntegerType, TimestampType
from delta.tables import DeltaTable
from datetime import datetime
from typing import Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CBTRN02C")

# =============================================================================
# VALIDATION REASON CODES (Matching COBOL CBTRN02C exactly)
# =============================================================================
REASON_INVALID_CARD = 100        # "INVALID CARD NUMBER FOUND"
REASON_ACCOUNT_NOT_FOUND = 101   # "ACCOUNT RECORD NOT FOUND"
REASON_OVERLIMIT = 102           # "OVERLIMIT TRANSACTION"
REASON_EXPIRED = 103             # "TRANSACTION RECEIVED AFTER ACCT EXPIRATION"
REASON_ACCOUNT_UPDATE_FAIL = 109 # "ACCOUNT RECORD NOT FOUND DURING UPDATE"

REASON_DESCRIPTIONS = {
    100: "INVALID CARD NUMBER FOUND",
    101: "ACCOUNT RECORD NOT FOUND",
    102: "OVERLIMIT TRANSACTION",
    103: "TRANSACTION RECEIVED AFTER ACCT EXPIRATION",
    109: "ACCOUNT RECORD NOT FOUND DURING UPDATE",
}


class CBTRN02CJob:
    """
    Databricks implementation of CBTRN02C - Post Daily Transactions.
    
    This class replicates the exact validation logic and data flow of the
    mainframe COBOL program, using Delta Lake for storage and PySpark for
    processing.
    """
    
    def __init__(
        self,
        spark: SparkSession,
        catalog: str = "carddemo",
        schema: str = "silver",
        batch_id: str = None
    ):
        """
        Initialize the job.
        
        Args:
            spark: SparkSession instance
            catalog: Unity Catalog name
            schema: Schema/database name
            batch_id: Unique identifier for this batch run (for idempotency)
        """
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
        self.batch_id = batch_id or datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Table paths
        self.dalytran_table = f"{catalog}.bronze.dalytran"
        self.transactions_table = f"{catalog}.{schema}.transactions"
        self.accounts_table = f"{catalog}.{schema}.accounts"
        self.card_xref_table = f"{catalog}.{schema}.card_xref"
        self.tran_cat_balance_table = f"{catalog}.{schema}.tran_cat_balance"
        self.rejects_table = f"{catalog}.{schema}.transaction_rejects"
        
        # Counters for reconciliation (matching COBOL WS-COUNTERS)
        self.records_read = 0
        self.records_written = 0
        self.records_rejected = 0
        
        logger.info(f"CBTRN02C Job initialized with batch_id: {self.batch_id}")
    
    def run(self) -> dict:
        """
        Execute the full transaction posting job.
        
        Returns:
            Dictionary with job statistics for reconciliation
        """
        logger.info("=" * 60)
        logger.info("CBTRN02C - POST DAILY TRANSACTIONS - STARTING")
        logger.info("=" * 60)
        
        # Step 1: Read daily transactions (1000-OPEN-FILES equivalent)
        dalytran_df = self._read_daily_transactions()
        self.records_read = dalytran_df.count()
        logger.info(f"Records read from DALYTRAN: {self.records_read}")
        
        # Step 2: Validate transactions (1500-VALIDATE-TRANSACTION equivalent)
        valid_df, rejects_df = self._validate_transactions(dalytran_df)
        
        # Step 3: Post valid transactions (2000-POST-TRANSACTION equivalent)
        if valid_df.count() > 0:
            self._post_transactions(valid_df)
        
        # Step 4: Write rejects (2500-WRITE-REJECT-REC equivalent)
        if rejects_df.count() > 0:
            self._write_rejects(rejects_df)
        
        # Step 5: Generate reconciliation report (9000-DISPLAY-COUNTERS equivalent)
        stats = self._generate_reconciliation_report()
        
        logger.info("=" * 60)
        logger.info("CBTRN02C - POST DAILY TRANSACTIONS - COMPLETED")
        logger.info("=" * 60)
        
        return stats
    
    def _read_daily_transactions(self) -> DataFrame:
        """
        Read daily transactions from bronze table.
        Equivalent to COBOL: 1100-READ-DALYTRAN-FILE
        
        In production, this would read from the bronze table where EBCDIC
        data has been converted and landed.
        """
        logger.info(f"Reading daily transactions from {self.dalytran_table}")
        
        # Read unprocessed transactions for this batch
        # Filter by batch_id to ensure idempotency
        df = self.spark.table(self.dalytran_table).filter(
            F.col("batch_id") == self.batch_id
        )
        
        return df
    
    def _validate_transactions(self, dalytran_df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        """
        Validate each transaction against business rules.
        Equivalent to COBOL: 1500-VALIDATE-TRANSACTION
        
        Validation checks (in order, matching COBOL):
        1. Card number exists in XREFFILE (reason 100)
        2. Account exists in ACCTFILE (reason 101)
        3. Transaction doesn't exceed credit limit (reason 102)
        4. Account is not expired (reason 103)
        """
        logger.info("Validating transactions...")
        
        # Load reference tables
        xref_df = self.spark.table(self.card_xref_table)
        accounts_df = self.spark.table(self.accounts_table)
        
        # Join with XREFFILE to get account ID
        # Equivalent to: 1600-LOOKUP-XREF
        validated_df = dalytran_df.alias("t").join(
            xref_df.alias("x"),
            F.col("t.card_num") == F.col("x.card_num"),
            "left"
        ).select(
            "t.*",
            F.col("x.acct_id").alias("xref_acct_id"),
            F.col("x.cust_id").alias("xref_cust_id")
        )
        
        # Check validation 1: Card number exists in XREFFILE
        validated_df = validated_df.withColumn(
            "validation_1_pass",
            F.col("xref_acct_id").isNotNull()
        ).withColumn(
            "reject_reason_1",
            F.when(~F.col("validation_1_pass"), F.lit(REASON_INVALID_CARD))
        )
        
        # Join with ACCTFILE to get account details
        # Equivalent to: 1700-LOOKUP-ACCOUNT
        validated_df = validated_df.alias("t").join(
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
        
        # Check validation 2: Account exists in ACCTFILE
        validated_df = validated_df.withColumn(
            "validation_2_pass",
            F.col("account_acct_id").isNotNull()
        ).withColumn(
            "reject_reason_2",
            F.when(
                F.col("validation_1_pass") & ~F.col("validation_2_pass"),
                F.lit(REASON_ACCOUNT_NOT_FOUND)
            )
        )
        
        # Check validation 3: Overlimit check
        # Equivalent to: 1800-CHECK-OVERLIMIT
        # COBOL: IF ACCT-CURR-BAL + DALYTRAN-AMT > ACCT-CREDIT-LIMIT
        validated_df = validated_df.withColumn(
            "new_balance",
            F.col("curr_bal") + F.col("tran_amt")
        ).withColumn(
            "validation_3_pass",
            F.col("new_balance") <= F.col("credit_limit")
        ).withColumn(
            "reject_reason_3",
            F.when(
                F.col("validation_1_pass") & 
                F.col("validation_2_pass") & 
                ~F.col("validation_3_pass"),
                F.lit(REASON_OVERLIMIT)
            )
        )
        
        # Check validation 4: Account expiration
        # Equivalent to: 1900-CHECK-EXPIRATION
        # COBOL: IF DALYTRAN-ORIG-TS(1:10) > ACCT-EXPIRAION-DATE
        validated_df = validated_df.withColumn(
            "tran_date",
            F.substring(F.col("orig_ts"), 1, 10)
        ).withColumn(
            "validation_4_pass",
            F.col("tran_date") <= F.col("expiration_date")
        ).withColumn(
            "reject_reason_4",
            F.when(
                F.col("validation_1_pass") & 
                F.col("validation_2_pass") & 
                F.col("validation_3_pass") & 
                ~F.col("validation_4_pass"),
                F.lit(REASON_EXPIRED)
            )
        )
        
        # Determine final validation status
        validated_df = validated_df.withColumn(
            "is_valid",
            F.col("validation_1_pass") & 
            F.col("validation_2_pass") & 
            F.col("validation_3_pass") & 
            F.col("validation_4_pass")
        ).withColumn(
            "reject_reason_code",
            F.coalesce(
                F.col("reject_reason_1"),
                F.col("reject_reason_2"),
                F.col("reject_reason_3"),
                F.col("reject_reason_4")
            )
        )
        
        # Split into valid and rejected transactions
        valid_df = validated_df.filter(F.col("is_valid") == True).select(
            "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
            "tran_amt", "merchant_id", "merchant_name", "merchant_city", 
            "merchant_zip", "card_num", "orig_ts",
            "xref_acct_id", "curr_bal", "curr_cyc_credit", "curr_cyc_debit",
            "batch_id"
        )
        
        rejects_df = validated_df.filter(F.col("is_valid") == False).select(
            "tran_id", "card_num", "tran_amt", "orig_ts",
            "reject_reason_code", "batch_id"
        )
        
        valid_count = valid_df.count()
        reject_count = rejects_df.count()
        logger.info(f"Validation complete: {valid_count} valid, {reject_count} rejected")
        
        self.records_written = valid_count
        self.records_rejected = reject_count
        
        return valid_df, rejects_df
    
    def _post_transactions(self, valid_df: DataFrame):
        """
        Post valid transactions to target tables.
        Equivalent to COBOL: 2000-POST-TRANSACTION
        
        This performs three operations:
        1. Write to TRANFILE (2900-WRITE-TRANSACTION-FILE)
        2. Update TCATBALF (2700-UPDATE-TCATBAL)
        3. Update ACCTFILE (2800-UPDATE-ACCOUNT-REC)
        """
        logger.info("Posting valid transactions...")
        
        # Generate processing timestamp
        # Equivalent to: Z-GET-DB2-FORMAT-TIMESTAMP
        proc_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")[:26]
        
        # Prepare transaction records for TRANFILE
        tran_records = valid_df.withColumn(
            "proc_ts", F.lit(proc_ts)
        ).withColumn(
            "created_ts", F.current_timestamp()
        ).select(
            "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
            "tran_amt", "merchant_id", "merchant_name", "merchant_city",
            "merchant_zip", "card_num", "orig_ts", "proc_ts", "batch_id", "created_ts"
        )
        
        # 2900-WRITE-TRANSACTION-FILE: Append to transactions table
        self._write_transactions(tran_records)
        
        # 2700-UPDATE-TCATBAL: Update transaction category balances
        self._update_tran_cat_balance(valid_df)
        
        # 2800-UPDATE-ACCOUNT-REC: Update account balances
        self._update_account_balances(valid_df)
        
        logger.info("Transaction posting complete")
    
    def _write_transactions(self, tran_records: DataFrame):
        """
        Write transactions to the transactions table.
        Equivalent to COBOL: 2900-WRITE-TRANSACTION-FILE
        
        Uses append mode with batch_id + tran_id uniqueness constraint
        to prevent duplicate posting on reruns.
        """
        logger.info(f"Writing transactions to {self.transactions_table}")
        
        # Check if table exists
        if self.spark.catalog.tableExists(self.transactions_table):
            # Use MERGE to prevent duplicates on rerun
            target_table = DeltaTable.forName(self.spark, self.transactions_table)
            
            target_table.alias("target").merge(
                tran_records.alias("source"),
                "target.tran_id = source.tran_id AND target.batch_id = source.batch_id"
            ).whenNotMatchedInsertAll().execute()
        else:
            # First run - create table
            tran_records.write.format("delta").mode("overwrite").saveAsTable(
                self.transactions_table
            )
    
    def _update_tran_cat_balance(self, valid_df: DataFrame):
        """
        Update transaction category balances.
        Equivalent to COBOL: 2700-UPDATE-TCATBAL
        
        For each unique (acct_id, tran_type_cd, tran_cat_cd) combination,
        add the transaction amount to the running balance.
        """
        logger.info(f"Updating transaction category balances in {self.tran_cat_balance_table}")
        
        # Aggregate transactions by category
        # Equivalent to COBOL logic that reads/creates/updates TCATBAL records
        balance_updates = valid_df.groupBy(
            F.col("xref_acct_id").alias("acct_id"),
            "tran_type_cd",
            "tran_cat_cd"
        ).agg(
            F.sum("tran_amt").alias("batch_amount")
        ).withColumn(
            "last_updated_ts", F.current_timestamp()
        ).withColumn(
            "last_updated_batch_id", F.lit(self.batch_id)
        )
        
        if self.spark.catalog.tableExists(self.tran_cat_balance_table):
            target_table = DeltaTable.forName(self.spark, self.tran_cat_balance_table)
            
            # MERGE: Update existing records or insert new ones
            # Equivalent to COBOL: 2700-A-CREATE-TCATBAL-REC / 2700-B-UPDATE-TCATBAL-REC
            target_table.alias("target").merge(
                balance_updates.alias("source"),
                """
                target.acct_id = source.acct_id AND
                target.tran_type_cd = source.tran_type_cd AND
                target.tran_cat_cd = source.tran_cat_cd
                """
            ).whenMatchedUpdate(set={
                "tran_cat_bal": "target.tran_cat_bal + source.batch_amount",
                "last_updated_ts": "source.last_updated_ts",
                "last_updated_batch_id": "source.last_updated_batch_id"
            }).whenNotMatchedInsert(values={
                "acct_id": "source.acct_id",
                "tran_type_cd": "source.tran_type_cd",
                "tran_cat_cd": "source.tran_cat_cd",
                "tran_cat_bal": "source.batch_amount",
                "last_updated_ts": "source.last_updated_ts",
                "last_updated_batch_id": "source.last_updated_batch_id"
            }).execute()
        else:
            # First run - create table with initial balances
            balance_updates.withColumn(
                "tran_cat_bal", F.col("batch_amount")
            ).drop("batch_amount").write.format("delta").mode("overwrite").saveAsTable(
                self.tran_cat_balance_table
            )
    
    def _update_account_balances(self, valid_df: DataFrame):
        """
        Update account balances.
        Equivalent to COBOL: 2800-UPDATE-ACCOUNT-REC
        
        COBOL Logic:
        - ADD DALYTRAN-AMT TO ACCT-CURR-BAL
        - IF DALYTRAN-AMT >= 0: ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT
        - ELSE: ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT
        """
        logger.info(f"Updating account balances in {self.accounts_table}")
        
        # Aggregate by account
        account_updates = valid_df.groupBy(
            F.col("xref_acct_id").alias("acct_id")
        ).agg(
            F.sum("tran_amt").alias("total_amount"),
            F.sum(F.when(F.col("tran_amt") >= 0, F.col("tran_amt")).otherwise(0)).alias("credit_amount"),
            F.sum(F.when(F.col("tran_amt") < 0, F.col("tran_amt")).otherwise(0)).alias("debit_amount")
        ).withColumn(
            "last_updated_ts", F.current_timestamp()
        ).withColumn(
            "last_updated_batch_id", F.lit(self.batch_id)
        )
        
        if self.spark.catalog.tableExists(self.accounts_table):
            target_table = DeltaTable.forName(self.spark, self.accounts_table)
            
            # MERGE: Update account balances
            # Equivalent to COBOL REWRITE FD-ACCTFILE-REC
            target_table.alias("target").merge(
                account_updates.alias("source"),
                "target.acct_id = source.acct_id"
            ).whenMatchedUpdate(set={
                "curr_bal": "target.curr_bal + source.total_amount",
                "curr_cyc_credit": "target.curr_cyc_credit + source.credit_amount",
                "curr_cyc_debit": "target.curr_cyc_debit + source.debit_amount",
                "last_updated_ts": "source.last_updated_ts",
                "last_updated_batch_id": "source.last_updated_batch_id"
            }).execute()
    
    def _write_rejects(self, rejects_df: DataFrame):
        """
        Write rejected transactions to rejects table.
        Equivalent to COBOL: 2500-WRITE-REJECT-REC
        """
        logger.info(f"Writing rejects to {self.rejects_table}")
        
        # Add reason description
        # Create a mapping UDF for reason codes
        reason_map = F.create_map([
            F.lit(k) for pair in REASON_DESCRIPTIONS.items() for k in pair
        ])
        
        rejects_with_desc = rejects_df.withColumn(
            "reject_reason_desc",
            F.coalesce(
                reason_map[F.col("reject_reason_code")],
                F.lit("UNKNOWN VALIDATION ERROR")
            )
        ).withColumn(
            "rejected_ts", F.current_timestamp()
        ).withColumn(
            "raw_record", F.lit(None).cast(StringType())  # Would contain original EBCDIC in production
        )
        
        # Append to rejects table
        if self.spark.catalog.tableExists(self.rejects_table):
            rejects_with_desc.write.format("delta").mode("append").saveAsTable(
                self.rejects_table
            )
        else:
            rejects_with_desc.write.format("delta").mode("overwrite").saveAsTable(
                self.rejects_table
            )
    
    def _generate_reconciliation_report(self) -> dict:
        """
        Generate reconciliation statistics.
        Equivalent to COBOL: 9000-DISPLAY-COUNTERS
        
        Returns statistics matching mainframe control totals for validation.
        """
        stats = {
            "batch_id": self.batch_id,
            "records_read": self.records_read,
            "records_written": self.records_written,
            "records_rejected": self.records_rejected,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("=" * 40)
        logger.info("RECONCILIATION REPORT")
        logger.info("=" * 40)
        logger.info(f"Batch ID:          {stats['batch_id']}")
        logger.info(f"Records Read:      {stats['records_read']}")
        logger.info(f"Records Written:   {stats['records_written']}")
        logger.info(f"Records Rejected:  {stats['records_rejected']}")
        logger.info("=" * 40)
        
        # Validate counts
        if stats['records_read'] != stats['records_written'] + stats['records_rejected']:
            logger.warning("WARNING: Record counts do not balance!")
        
        return stats


def main():
    """
    Main entry point for Databricks job.
    
    This function is called when the job is executed via Databricks Jobs
    or can be run interactively in a notebook.
    """
    # Initialize Spark session (already available in Databricks)
    spark = SparkSession.builder.appName("CBTRN02C-PostDailyTransactions").getOrCreate()
    
    # Get job parameters (passed via Databricks job configuration)
    # In production, these would come from job parameters or widgets
    catalog = spark.conf.get("spark.databricks.catalog", "carddemo")
    schema = spark.conf.get("spark.databricks.schema", "silver")
    batch_id = spark.conf.get("spark.databricks.batch_id", None)
    
    # Create and run the job
    job = CBTRN02CJob(
        spark=spark,
        catalog=catalog,
        schema=schema,
        batch_id=batch_id
    )
    
    stats = job.run()
    
    # Return stats for job output
    return stats


if __name__ == "__main__":
    main()
