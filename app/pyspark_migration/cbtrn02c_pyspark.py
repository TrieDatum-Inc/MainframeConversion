# Databricks notebook source
# MAGIC %md
# MAGIC # CBTRN02C - Transaction Posting Program (PySpark Migration)
# MAGIC 
# MAGIC This is a PySpark migration of the COBOL batch program CBTRN02C.cbl.
# MAGIC 
# MAGIC ## Original COBOL Program Function:
# MAGIC Post records from daily transaction file to transaction master, update account 
# MAGIC balances, and maintain transaction category balances.
# MAGIC 
# MAGIC ## Processing Logic (Sequential - matches COBOL behavior):
# MAGIC 1. Read daily transactions sequentially
# MAGIC 2. For each transaction:
# MAGIC    - Validate card number exists in cross-reference
# MAGIC    - Validate account exists and check credit limit/expiration
# MAGIC    - If valid: Post transaction, update balances
# MAGIC    - If invalid: Write to rejects with failure reason
# MAGIC 3. Display processing statistics
# MAGIC 
# MAGIC ## Validation Error Codes:
# MAGIC - 100: Invalid card number (not found in cross-reference)
# MAGIC - 101: Account record not found
# MAGIC - 102: Overlimit transaction
# MAGIC - 103: Transaction received after account expiration

# COMMAND ----------

from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import (
    col, lit, current_timestamp, when, coalesce
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType, 
    IntegerType, LongType, TimestampType, DateType
)
from datetime import datetime
from decimal import Decimal
import sys

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

class CBTRN02CConfig:
    """Configuration for the CBTRN02C transaction posting program."""
    
    # Database name
    DATABASE_NAME = "carddemo"
    
    # Table names
    DAILY_TRANSACTIONS_TABLE = "daily_transactions"
    CARD_XREF_TABLE = "card_xref"
    ACCOUNTS_TABLE = "accounts"
    TCATBAL_TABLE = "transaction_category_balance"
    TRANSACTIONS_TABLE = "transactions"
    DAILY_REJECTS_TABLE = "daily_rejects"
    
    # Validation error codes (matching COBOL program)
    ERROR_INVALID_CARD = 100
    ERROR_ACCOUNT_NOT_FOUND = 101
    ERROR_OVERLIMIT = 102
    ERROR_EXPIRED_ACCOUNT = 103
    
    # Error descriptions
    ERROR_DESCRIPTIONS = {
        100: "INVALID CARD NUMBER FOUND",
        101: "ACCOUNT RECORD NOT FOUND",
        102: "OVERLIMIT TRANSACTION",
        103: "TRANSACTION RECEIVED AFTER ACCT EXPIRATION"
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ## CBTRN02C Transaction Posting Class

# COMMAND ----------

class CBTRN02C:
    """
    PySpark implementation of CBTRN02C COBOL batch program.
    
    This class processes daily transactions sequentially, validating each
    transaction and either posting it to the transaction master or writing
    it to the rejects file with a failure reason.
    """
    
    def __init__(self, spark: SparkSession, config: CBTRN02CConfig = None):
        """Initialize the transaction posting program."""
        self.spark = spark
        self.config = config or CBTRN02CConfig()
        
        # Counters (equivalent to WS-COUNTERS in COBOL)
        self.transaction_count = 0
        self.reject_count = 0
        self.posted_count = 0
        
        # Set database context
        self.spark.sql(f"USE {self.config.DATABASE_NAME}")
        
        # Cache lookup tables for performance
        self._load_lookup_tables()
        
        print("START OF EXECUTION OF PROGRAM CBTRN02C")
    
    def _load_lookup_tables(self):
        """Load lookup tables into memory for efficient access."""
        # Load card cross-reference as dictionary for O(1) lookup
        xref_df = self.spark.table(self.config.CARD_XREF_TABLE).collect()
        self.card_xref_dict = {
            row.card_num: {"cust_id": row.cust_id, "acct_id": row.acct_id}
            for row in xref_df
        }
        
        # Load accounts as dictionary for O(1) lookup
        accounts_df = self.spark.table(self.config.ACCOUNTS_TABLE).collect()
        self.accounts_dict = {
            row.acct_id: {
                "acct_active_status": row.acct_active_status,
                "acct_curr_bal": row.acct_curr_bal,
                "acct_credit_limit": row.acct_credit_limit,
                "acct_expiration_date": row.acct_expiration_date,
                "acct_curr_cyc_credit": row.acct_curr_cyc_credit,
                "acct_curr_cyc_debit": row.acct_curr_cyc_debit
            }
            for row in accounts_df
        }
        
        # Load transaction category balances as dictionary
        tcatbal_df = self.spark.table(self.config.TCATBAL_TABLE).collect()
        self.tcatbal_dict = {
            (row.acct_id, row.tran_type_cd, row.tran_cat_cd): row.tran_cat_bal
            for row in tcatbal_df
        }
        
        print(f"Loaded {len(self.card_xref_dict)} card cross-references")
        print(f"Loaded {len(self.accounts_dict)} accounts")
        print(f"Loaded {len(self.tcatbal_dict)} category balances")
    
    def _validate_transaction(self, tran: Row) -> tuple:
        """
        Validate a transaction (equivalent to 1500-VALIDATE-TRAN).
        
        Returns:
            tuple: (is_valid, error_code, error_desc, acct_id)
        """
        # 1500-A-LOOKUP-XREF: Validate card number exists
        card_num = tran.card_num
        if card_num not in self.card_xref_dict:
            return (False, self.config.ERROR_INVALID_CARD, 
                    self.config.ERROR_DESCRIPTIONS[self.config.ERROR_INVALID_CARD], None)
        
        xref = self.card_xref_dict[card_num]
        acct_id = xref["acct_id"]
        
        # 1500-B-LOOKUP-ACCT: Validate account exists
        if acct_id not in self.accounts_dict:
            return (False, self.config.ERROR_ACCOUNT_NOT_FOUND,
                    self.config.ERROR_DESCRIPTIONS[self.config.ERROR_ACCOUNT_NOT_FOUND], None)
        
        account = self.accounts_dict[acct_id]
        
        # Check credit limit (Error 102)
        # COBOL: COMPUTE WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
        curr_cyc_credit = account["acct_curr_cyc_credit"] or Decimal("0")
        curr_cyc_debit = account["acct_curr_cyc_debit"] or Decimal("0")
        tran_amt = tran.tran_amt or Decimal("0")
        
        temp_bal = curr_cyc_credit - curr_cyc_debit + tran_amt
        credit_limit = account["acct_credit_limit"]
        
        if credit_limit < temp_bal:
            return (False, self.config.ERROR_OVERLIMIT,
                    self.config.ERROR_DESCRIPTIONS[self.config.ERROR_OVERLIMIT], acct_id)
        
        # Check account expiration (Error 103)
        # COBOL: IF ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS (1:10)
        expiration_date = account["acct_expiration_date"]
        tran_date = tran.orig_ts.date() if tran.orig_ts else None
        
        if expiration_date and tran_date and expiration_date < tran_date:
            return (False, self.config.ERROR_EXPIRED_ACCOUNT,
                    self.config.ERROR_DESCRIPTIONS[self.config.ERROR_EXPIRED_ACCOUNT], acct_id)
        
        return (True, 0, "", acct_id)
    
    def _update_tcatbal(self, acct_id: int, tran_type_cd: str, tran_cat_cd: int, tran_amt: Decimal):
        """
        Update transaction category balance (equivalent to 2700-UPDATE-TCATBAL).
        
        Creates new record if not exists, otherwise updates existing balance.
        """
        key = (acct_id, tran_type_cd, tran_cat_cd)
        
        if key in self.tcatbal_dict:
            # 2700-B-UPDATE-TCATBAL-REC: Update existing record
            self.tcatbal_dict[key] = self.tcatbal_dict[key] + tran_amt
        else:
            # 2700-A-CREATE-TCATBAL-REC: Create new record
            self.tcatbal_dict[key] = tran_amt
            print(f"TCATBAL record not found for key: {key}.. Creating.")
    
    def _update_account(self, acct_id: int, tran_amt: Decimal):
        """
        Update account balances (equivalent to 2800-UPDATE-ACCOUNT-REC).
        
        Updates current balance and cycle credits/debits.
        """
        account = self.accounts_dict[acct_id]
        
        # ADD DALYTRAN-AMT TO ACCT-CURR-BAL
        account["acct_curr_bal"] = (account["acct_curr_bal"] or Decimal("0")) + tran_amt
        
        # IF DALYTRAN-AMT >= 0: ADD TO ACCT-CURR-CYC-CREDIT
        # ELSE: ADD TO ACCT-CURR-CYC-DEBIT
        if tran_amt >= 0:
            account["acct_curr_cyc_credit"] = (account["acct_curr_cyc_credit"] or Decimal("0")) + tran_amt
        else:
            account["acct_curr_cyc_debit"] = (account["acct_curr_cyc_debit"] or Decimal("0")) + tran_amt
        
        self.accounts_dict[acct_id] = account
    
    def _post_transaction(self, tran: Row, acct_id: int) -> dict:
        """
        Post a valid transaction (equivalent to 2000-POST-TRANSACTION).
        
        Returns the transaction record to be written.
        """
        proc_ts = datetime.now()
        
        # Update transaction category balance
        self._update_tcatbal(acct_id, tran.tran_type_cd, tran.tran_cat_cd, tran.tran_amt)
        
        # Update account record
        self._update_account(acct_id, tran.tran_amt)
        
        # Return transaction record for writing
        return {
            "tran_id": tran.tran_id,
            "tran_type_cd": tran.tran_type_cd,
            "tran_cat_cd": tran.tran_cat_cd,
            "tran_source": tran.tran_source,
            "tran_desc": tran.tran_desc,
            "tran_amt": tran.tran_amt,
            "merchant_id": tran.merchant_id,
            "merchant_name": tran.merchant_name,
            "merchant_city": tran.merchant_city,
            "merchant_zip": tran.merchant_zip,
            "card_num": tran.card_num,
            "orig_ts": tran.orig_ts,
            "proc_ts": proc_ts
        }
    
    def _write_reject(self, tran: Row, error_code: int, error_desc: str) -> dict:
        """
        Write a rejected transaction (equivalent to 2500-WRITE-REJECT-REC).
        
        Returns the reject record to be written.
        """
        return {
            "tran_id": tran.tran_id,
            "tran_type_cd": tran.tran_type_cd,
            "tran_cat_cd": tran.tran_cat_cd,
            "tran_source": tran.tran_source,
            "tran_desc": tran.tran_desc,
            "tran_amt": tran.tran_amt,
            "merchant_id": tran.merchant_id,
            "merchant_name": tran.merchant_name,
            "merchant_city": tran.merchant_city,
            "merchant_zip": tran.merchant_zip,
            "card_num": tran.card_num,
            "orig_ts": tran.orig_ts,
            "validation_fail_reason": error_code,
            "validation_fail_reason_desc": error_desc,
            "reject_ts": datetime.now()
        }
    
    def run(self) -> int:
        """
        Execute the transaction posting program.
        
        This is the main entry point, equivalent to PROCEDURE DIVISION.
        
        Returns:
            int: Return code (0 = success, 4 = completed with rejects)
        """
        # Lists to collect records for batch writing
        posted_transactions = []
        rejected_transactions = []
        processed_tran_ids = []
        
        # Read daily transactions (equivalent to 1000-DALYTRAN-GET-NEXT)
        daily_trans_df = self.spark.table(self.config.DAILY_TRANSACTIONS_TABLE) \
            .filter(col("processed_flag") == "N") \
            .orderBy("tran_id")
        
        # Collect for sequential processing (matching COBOL behavior)
        daily_transactions = daily_trans_df.collect()
        
        print(f"\nProcessing {len(daily_transactions)} unprocessed transactions...")
        print("-" * 60)
        
        # Process each transaction sequentially
        for tran in daily_transactions:
            self.transaction_count += 1
            
            # Validate transaction (1500-VALIDATE-TRAN)
            is_valid, error_code, error_desc, acct_id = self._validate_transaction(tran)
            
            if is_valid:
                # Post transaction (2000-POST-TRANSACTION)
                posted_record = self._post_transaction(tran, acct_id)
                posted_transactions.append(posted_record)
                processed_tran_ids.append(tran.tran_id)
                self.posted_count += 1
                print(f"  POSTED: {tran.tran_id} - Amount: {tran.tran_amt}")
            else:
                # Write reject (2500-WRITE-REJECT-REC)
                reject_record = self._write_reject(tran, error_code, error_desc)
                rejected_transactions.append(reject_record)
                processed_tran_ids.append(tran.tran_id)
                self.reject_count += 1
                print(f"  REJECTED: {tran.tran_id} - Error {error_code}: {error_desc}")
        
        print("-" * 60)
        
        # Write posted transactions to transactions table
        if posted_transactions:
            self._write_transactions(posted_transactions)
        
        # Write rejected transactions to daily_rejects table
        if rejected_transactions:
            self._write_rejects(rejected_transactions)
        
        # Update processed flag on daily_transactions
        if processed_tran_ids:
            self._mark_transactions_processed(processed_tran_ids)
        
        # Persist updated account balances
        self._persist_account_updates()
        
        # Persist updated category balances
        self._persist_tcatbal_updates()
        
        # Display statistics
        print(f"\nTRANSACTIONS PROCESSED :{self.transaction_count:09d}")
        print(f"TRANSACTIONS POSTED   :{self.posted_count:09d}")
        print(f"TRANSACTIONS REJECTED :{self.reject_count:09d}")
        
        # Set return code
        return_code = 4 if self.reject_count > 0 else 0
        
        print(f"\nEND OF EXECUTION OF PROGRAM CBTRN02C")
        print(f"RETURN CODE: {return_code}")
        
        return return_code
    
    def _write_transactions(self, transactions: list):
        """Write posted transactions to the transactions table."""
        schema = StructType([
            StructField("tran_id", StringType(), False),
            StructField("tran_type_cd", StringType(), False),
            StructField("tran_cat_cd", IntegerType(), False),
            StructField("tran_source", StringType(), True),
            StructField("tran_desc", StringType(), True),
            StructField("tran_amt", DecimalType(11, 2), False),
            StructField("merchant_id", LongType(), True),
            StructField("merchant_name", StringType(), True),
            StructField("merchant_city", StringType(), True),
            StructField("merchant_zip", StringType(), True),
            StructField("card_num", StringType(), False),
            StructField("orig_ts", TimestampType(), False),
            StructField("proc_ts", TimestampType(), False)
        ])
        
        df = self.spark.createDataFrame(transactions, schema)
        df.write.format("delta").mode("append").saveAsTable(
            f"{self.config.DATABASE_NAME}.{self.config.TRANSACTIONS_TABLE}"
        )
        print(f"\nWrote {len(transactions)} records to transactions table")
    
    def _write_rejects(self, rejects: list):
        """Write rejected transactions to the daily_rejects table."""
        schema = StructType([
            StructField("tran_id", StringType(), False),
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
            StructField("orig_ts", TimestampType(), True),
            StructField("validation_fail_reason", IntegerType(), False),
            StructField("validation_fail_reason_desc", StringType(), False),
            StructField("reject_ts", TimestampType(), True)
        ])
        
        df = self.spark.createDataFrame(rejects, schema)
        df.write.format("delta").mode("append").saveAsTable(
            f"{self.config.DATABASE_NAME}.{self.config.DAILY_REJECTS_TABLE}"
        )
        print(f"Wrote {len(rejects)} records to daily_rejects table")
    
    def _mark_transactions_processed(self, tran_ids: list):
        """Mark processed transactions in daily_transactions table."""
        tran_ids_str = ",".join([f"'{tid}'" for tid in tran_ids])
        
        self.spark.sql(f"""
            UPDATE {self.config.DATABASE_NAME}.{self.config.DAILY_TRANSACTIONS_TABLE}
            SET processed_flag = 'Y',
                proc_ts = current_timestamp()
            WHERE tran_id IN ({tran_ids_str})
        """)
        print(f"Marked {len(tran_ids)} transactions as processed")
    
    def _persist_account_updates(self):
        """Persist updated account balances to the accounts table."""
        for acct_id, account in self.accounts_dict.items():
            self.spark.sql(f"""
                UPDATE {self.config.DATABASE_NAME}.{self.config.ACCOUNTS_TABLE}
                SET acct_curr_bal = {account['acct_curr_bal']},
                    acct_curr_cyc_credit = {account['acct_curr_cyc_credit']},
                    acct_curr_cyc_debit = {account['acct_curr_cyc_debit']}
                WHERE acct_id = {acct_id}
            """)
        print(f"Updated {len(self.accounts_dict)} account records")
    
    def _persist_tcatbal_updates(self):
        """Persist updated category balances to the transaction_category_balance table."""
        # First, get existing keys
        existing_df = self.spark.table(self.config.TCATBAL_TABLE).collect()
        existing_keys = {
            (row.acct_id, row.tran_type_cd, row.tran_cat_cd)
            for row in existing_df
        }
        
        updates = []
        inserts = []
        
        for key, balance in self.tcatbal_dict.items():
            acct_id, tran_type_cd, tran_cat_cd = key
            if key in existing_keys:
                updates.append((acct_id, tran_type_cd, tran_cat_cd, balance))
            else:
                inserts.append((acct_id, tran_type_cd, tran_cat_cd, balance))
        
        # Update existing records
        for acct_id, tran_type_cd, tran_cat_cd, balance in updates:
            self.spark.sql(f"""
                UPDATE {self.config.DATABASE_NAME}.{self.config.TCATBAL_TABLE}
                SET tran_cat_bal = {balance}
                WHERE acct_id = {acct_id}
                  AND tran_type_cd = '{tran_type_cd}'
                  AND tran_cat_cd = {tran_cat_cd}
            """)
        
        # Insert new records
        if inserts:
            schema = StructType([
                StructField("acct_id", LongType(), False),
                StructField("tran_type_cd", StringType(), False),
                StructField("tran_cat_cd", IntegerType(), False),
                StructField("tran_cat_bal", DecimalType(11, 2), True)
            ])
            
            insert_df = self.spark.createDataFrame(inserts, schema)
            insert_df.write.format("delta").mode("append").saveAsTable(
                f"{self.config.DATABASE_NAME}.{self.config.TCATBAL_TABLE}"
            )
        
        print(f"Updated {len(updates)} and inserted {len(inserts)} category balance records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Program (when run as notebook)

# COMMAND ----------

# Main execution
if __name__ == "__main__" or "dbutils" in dir():
    # Initialize and run the program
    config = CBTRN02CConfig()
    program = CBTRN02C(spark, config)
    return_code = program.run()
    
    # In Databricks, we can use dbutils to exit with return code
    # For notebook execution, just display the result
    print(f"\n{'=' * 60}")
    print(f"PROGRAM COMPLETED WITH RETURN CODE: {return_code}")
    print(f"{'=' * 60}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Results

# COMMAND ----------

# Display posted transactions
print("Posted Transactions:")
spark.sql("SELECT * FROM transactions ORDER BY tran_id").show(truncate=False)

# COMMAND ----------

# Display rejected transactions
print("Rejected Transactions:")
spark.sql("""
    SELECT tran_id, card_num, tran_amt, 
           validation_fail_reason, validation_fail_reason_desc 
    FROM daily_rejects 
    ORDER BY tran_id
""").show(truncate=False)

# COMMAND ----------

# Display updated account balances
print("Updated Account Balances:")
spark.sql("""
    SELECT acct_id, acct_curr_bal, acct_credit_limit, 
           acct_curr_cyc_credit, acct_curr_cyc_debit 
    FROM accounts
""").show(truncate=False)

# COMMAND ----------

# Display updated category balances
print("Updated Category Balances:")
spark.sql("SELECT * FROM transaction_category_balance ORDER BY acct_id, tran_type_cd, tran_cat_cd").show(truncate=False)
