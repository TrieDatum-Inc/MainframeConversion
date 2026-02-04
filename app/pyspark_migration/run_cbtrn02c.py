# Databricks notebook source
# MAGIC %md
# MAGIC # CardDemo Transaction Posting - Runner Script
# MAGIC 
# MAGIC This script orchestrates the complete execution of the CBTRN02C transaction posting program.
# MAGIC 
# MAGIC ## Execution Steps:
# MAGIC 1. Verify database and tables exist
# MAGIC 2. Display pre-execution statistics
# MAGIC 3. Execute CBTRN02C transaction posting
# MAGIC 4. Display post-execution statistics and results
# MAGIC 
# MAGIC ## Usage:
# MAGIC Run this notebook in Databricks to execute the full transaction posting cycle.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Dependencies

# COMMAND ----------

from datetime import datetime
import sys

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

DATABASE_NAME = "carddemo"

# Verify database exists
try:
    spark.sql(f"USE {DATABASE_NAME}")
    print(f"Connected to database: {DATABASE_NAME}")
except Exception as e:
    print(f"ERROR: Database '{DATABASE_NAME}' not found.")
    print("Please run 01_table_setup.py first to create the database and tables.")
    raise e

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pre-Execution Statistics

# COMMAND ----------

def display_statistics(title: str):
    """Display current table statistics."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)
    
    stats = {
        "Daily Transactions (Unprocessed)": spark.sql(
            "SELECT COUNT(*) FROM daily_transactions WHERE processed_flag = 'N'"
        ).collect()[0][0],
        "Daily Transactions (Processed)": spark.sql(
            "SELECT COUNT(*) FROM daily_transactions WHERE processed_flag = 'Y'"
        ).collect()[0][0],
        "Card Cross-References": spark.sql("SELECT COUNT(*) FROM card_xref").collect()[0][0],
        "Accounts": spark.sql("SELECT COUNT(*) FROM accounts").collect()[0][0],
        "Category Balances": spark.sql("SELECT COUNT(*) FROM transaction_category_balance").collect()[0][0],
        "Posted Transactions": spark.sql("SELECT COUNT(*) FROM transactions").collect()[0][0],
        "Rejected Transactions": spark.sql("SELECT COUNT(*) FROM daily_rejects").collect()[0][0],
    }
    
    for name, count in stats.items():
        print(f"  {name:40s}: {count:,}")
    
    print("=" * 70)
    return stats

# Display pre-execution stats
pre_stats = display_statistics("PRE-EXECUTION STATISTICS")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Display Pending Transactions

# COMMAND ----------

print("\nPending Transactions to Process:")
print("-" * 70)
spark.sql("""
    SELECT tran_id, card_num, tran_amt, tran_desc
    FROM daily_transactions 
    WHERE processed_flag = 'N'
    ORDER BY tran_id
""").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute CBTRN02C Transaction Posting Program

# COMMAND ----------

# MAGIC %run ./cbtrn02c_pyspark

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alternative: Direct Execution (if %run doesn't work)
# MAGIC Uncomment and run the cell below if the %run command above doesn't work in your environment.

# COMMAND ----------

# # Alternative execution method - uncomment if needed
# exec(open("/Workspace/path/to/cbtrn02c_pyspark.py").read())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Post-Execution Statistics

# COMMAND ----------

post_stats = display_statistics("POST-EXECUTION STATISTICS")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execution Summary

# COMMAND ----------

print("\n" + "=" * 70)
print(" EXECUTION SUMMARY")
print("=" * 70)

# Calculate changes
transactions_processed = post_stats["Daily Transactions (Processed)"] - pre_stats["Daily Transactions (Processed)"]
transactions_posted = post_stats["Posted Transactions"] - pre_stats["Posted Transactions"]
transactions_rejected = post_stats["Rejected Transactions"] - pre_stats["Rejected Transactions"]
new_category_balances = post_stats["Category Balances"] - pre_stats["Category Balances"]

print(f"  Transactions Processed:     {transactions_processed:,}")
print(f"  Transactions Posted:        {transactions_posted:,}")
print(f"  Transactions Rejected:      {transactions_rejected:,}")
print(f"  New Category Balances:      {new_category_balances:,}")
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC ## View Posted Transactions

# COMMAND ----------

print("\nPosted Transactions:")
spark.sql("""
    SELECT tran_id, tran_type_cd, tran_cat_cd, tran_amt, 
           card_num, merchant_name, proc_ts
    FROM transactions 
    ORDER BY proc_ts DESC, tran_id
""").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## View Rejected Transactions

# COMMAND ----------

print("\nRejected Transactions:")
spark.sql("""
    SELECT tran_id, card_num, tran_amt, 
           validation_fail_reason as err_code,
           validation_fail_reason_desc as error_description,
           reject_ts
    FROM daily_rejects 
    ORDER BY reject_ts DESC, tran_id
""").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## View Updated Account Balances

# COMMAND ----------

print("\nAccount Balances After Processing:")
spark.sql("""
    SELECT 
        acct_id,
        acct_curr_bal as current_balance,
        acct_credit_limit as credit_limit,
        acct_curr_cyc_credit as cycle_credits,
        acct_curr_cyc_debit as cycle_debits,
        (acct_credit_limit - (acct_curr_cyc_credit - acct_curr_cyc_debit)) as available_credit
    FROM accounts
    ORDER BY acct_id
""").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## View Category Balances

# COMMAND ----------

print("\nTransaction Category Balances:")
spark.sql("""
    SELECT 
        acct_id,
        tran_type_cd,
        tran_cat_cd,
        tran_cat_bal as category_balance
    FROM transaction_category_balance
    ORDER BY acct_id, tran_type_cd, tran_cat_cd
""").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execution Complete

# COMMAND ----------

print("\n" + "=" * 70)
print(" CBTRN02C TRANSACTION POSTING COMPLETE")
print("=" * 70)
print(f" Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f" Database: {DATABASE_NAME}")
print("=" * 70)

# Return success indicator
if transactions_rejected > 0:
    print("\n WARNING: Some transactions were rejected. Review daily_rejects table.")
    # dbutils.notebook.exit("4")  # Uncomment for Databricks workflow integration
else:
    print("\n SUCCESS: All transactions processed successfully.")
    # dbutils.notebook.exit("0")  # Uncomment for Databricks workflow integration
