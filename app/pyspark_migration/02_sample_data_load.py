# Databricks notebook source
# MAGIC %md
# MAGIC # CardDemo Sample Data Load
# MAGIC This script loads sample data into the Delta tables for testing the CBTRN02C transaction posting program.
# MAGIC 
# MAGIC ## Data Loaded:
# MAGIC - card_xref: 5 card-to-account mappings
# MAGIC - accounts: 3 account records with various balances/limits
# MAGIC - transaction_category_balance: Initial category balances
# MAGIC - daily_transactions: 10 sample transactions (mix of valid and invalid)

# COMMAND ----------

from pyspark.sql import Row
from pyspark.sql.functions import lit, current_timestamp, to_timestamp
from datetime import datetime, date
from decimal import Decimal

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

DATABASE_NAME = "carddemo"
spark.sql(f"USE {DATABASE_NAME}")

print(f"Using database: {DATABASE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Clear Existing Data (Optional)
# MAGIC Uncomment to clear existing data before loading

# COMMAND ----------

# Clear all tables for fresh load
spark.sql("DELETE FROM daily_transactions")
spark.sql("DELETE FROM card_xref")
spark.sql("DELETE FROM accounts")
spark.sql("DELETE FROM transaction_category_balance")
spark.sql("DELETE FROM transactions")
spark.sql("DELETE FROM daily_rejects")

print("Cleared all existing data")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Card Cross-Reference Data (card_xref)
# MAGIC Maps card numbers to customer and account IDs

# COMMAND ----------

card_xref_data = [
    # card_num (16 chars), cust_id, acct_id
    ("4111111111111111", 100000001, 10000000001),
    ("4222222222222222", 100000002, 10000000002),
    ("4333333333333333", 100000003, 10000000003),
    ("4444444444444444", 100000001, 10000000001),  # Same account, different card
    ("4555555555555555", 100000002, 10000000002),  # Same account, different card
]

card_xref_df = spark.createDataFrame(card_xref_data, ["card_num", "cust_id", "acct_id"])

card_xref_df.write.format("delta").mode("append").saveAsTable("card_xref")

print(f"Loaded {len(card_xref_data)} records into card_xref")
spark.sql("SELECT * FROM card_xref").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Account Data (accounts)
# MAGIC Account master with balances and credit limits

# COMMAND ----------

accounts_data = [
    # acct_id, active_status, curr_bal, credit_limit, cash_limit, open_date, exp_date, reissue_date, cyc_credit, cyc_debit, zip, group_id
    (10000000001, "Y", Decimal("1500.00"), Decimal("5000.00"), Decimal("1000.00"), 
     date(2020, 1, 15), date(2027, 12, 31), date(2024, 1, 15), 
     Decimal("2000.00"), Decimal("500.00"), "10001", "GRP001"),
    
    (10000000002, "Y", Decimal("4800.00"), Decimal("5000.00"), Decimal("1000.00"), 
     date(2019, 6, 1), date(2026, 6, 30), date(2023, 6, 1), 
     Decimal("5000.00"), Decimal("200.00"), "20002", "GRP001"),
    
    (10000000003, "Y", Decimal("100.00"), Decimal("3000.00"), Decimal("500.00"), 
     date(2021, 3, 10), date(2024, 3, 31), date(2024, 3, 10),  # Expired account
     Decimal("500.00"), Decimal("400.00"), "30003", "GRP002"),
]

accounts_schema = [
    "acct_id", "acct_active_status", "acct_curr_bal", "acct_credit_limit", 
    "acct_cash_credit_limit", "acct_open_date", "acct_expiration_date", 
    "acct_reissue_date", "acct_curr_cyc_credit", "acct_curr_cyc_debit", 
    "acct_addr_zip", "acct_group_id"
]

accounts_df = spark.createDataFrame(accounts_data, accounts_schema)

accounts_df.write.format("delta").mode("append").saveAsTable("accounts")

print(f"Loaded {len(accounts_data)} records into accounts")
spark.sql("SELECT acct_id, acct_curr_bal, acct_credit_limit, acct_expiration_date FROM accounts").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Transaction Category Balance Data (transaction_category_balance)
# MAGIC Initial balances by account and category

# COMMAND ----------

tcatbal_data = [
    # acct_id, tran_type_cd, tran_cat_cd, tran_cat_bal
    (10000000001, "PR", 5001, Decimal("1200.00")),  # Purchase - Retail
    (10000000001, "PR", 5002, Decimal("300.00")),   # Purchase - Online
    (10000000002, "PR", 5001, Decimal("4500.00")),  # Purchase - Retail
    (10000000002, "CA", 6001, Decimal("200.00")),   # Cash Advance
]

tcatbal_df = spark.createDataFrame(tcatbal_data, ["acct_id", "tran_type_cd", "tran_cat_cd", "tran_cat_bal"])

tcatbal_df.write.format("delta").mode("append").saveAsTable("transaction_category_balance")

print(f"Loaded {len(tcatbal_data)} records into transaction_category_balance")
spark.sql("SELECT * FROM transaction_category_balance").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Daily Transactions (daily_transactions)
# MAGIC Mix of valid and invalid transactions to test all validation paths

# COMMAND ----------

# Sample daily transactions - mix of valid and invalid scenarios
daily_tran_data = [
    # Transaction 1: Valid purchase on account 1
    ("TRN20260204001", "PR", 5001, "POS", "Grocery Store Purchase", 
     Decimal("125.50"), 900001, "SuperMart", "New York", "10001",
     "4111111111111111", datetime(2026, 2, 4, 10, 30, 0), None, "N"),
    
    # Transaction 2: Valid purchase on account 1 (different card, same account)
    ("TRN20260204002", "PR", 5002, "ONLINE", "Amazon Purchase", 
     Decimal("89.99"), 900002, "Amazon.com", "Seattle", "98101",
     "4444444444444444", datetime(2026, 2, 4, 11, 15, 0), None, "N"),
    
    # Transaction 3: Valid purchase on account 2
    ("TRN20260204003", "PR", 5001, "POS", "Gas Station", 
     Decimal("45.00"), 900003, "Shell Gas", "Chicago", "60601",
     "4222222222222222", datetime(2026, 2, 4, 12, 0, 0), None, "N"),
    
    # Transaction 4: INVALID - Card number not in xref (Error 100)
    ("TRN20260204004", "PR", 5001, "POS", "Unknown Card Transaction", 
     Decimal("50.00"), 900004, "Test Store", "Boston", "02101",
     "9999999999999999", datetime(2026, 2, 4, 13, 0, 0), None, "N"),
    
    # Transaction 5: INVALID - Overlimit on account 2 (Error 102)
    # Account 2 has: credit_limit=5000, curr_cyc_credit=5000, curr_cyc_debit=200
    # Available = 5000 - (5000 - 200) = 200, but trying to charge 500
    ("TRN20260204005", "PR", 5001, "POS", "Overlimit Purchase Attempt", 
     Decimal("500.00"), 900005, "Luxury Store", "Miami", "33101",
     "4555555555555555", datetime(2026, 2, 4, 14, 0, 0), None, "N"),
    
    # Transaction 6: INVALID - Expired account (Error 103)
    # Account 3 expired on 2024-03-31
    ("TRN20260204006", "PR", 5001, "POS", "Expired Account Transaction", 
     Decimal("75.00"), 900006, "Corner Store", "Denver", "80201",
     "4333333333333333", datetime(2026, 2, 4, 15, 0, 0), None, "N"),
    
    # Transaction 7: Valid credit/refund on account 1 (negative amount)
    ("TRN20260204007", "CR", 5001, "POS", "Refund from SuperMart", 
     Decimal("-50.00"), 900001, "SuperMart", "New York", "10001",
     "4111111111111111", datetime(2026, 2, 4, 16, 0, 0), None, "N"),
    
    # Transaction 8: Valid cash advance on account 2
    ("TRN20260204008", "CA", 6001, "ATM", "ATM Cash Withdrawal", 
     Decimal("100.00"), 900007, "Chase ATM", "Chicago", "60602",
     "4222222222222222", datetime(2026, 2, 4, 17, 0, 0), None, "N"),
    
    # Transaction 9: Valid purchase - new category (will create new tcatbal record)
    ("TRN20260204009", "PR", 5003, "POS", "Restaurant Dinner", 
     Decimal("85.00"), 900008, "Fine Dining", "New York", "10002",
     "4111111111111111", datetime(2026, 2, 4, 18, 0, 0), None, "N"),
    
    # Transaction 10: Valid small purchase on account 1
    ("TRN20260204010", "PR", 5001, "POS", "Coffee Shop", 
     Decimal("5.75"), 900009, "Starbucks", "New York", "10001",
     "4111111111111111", datetime(2026, 2, 4, 19, 0, 0), None, "N"),
]

daily_tran_schema = [
    "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
    "tran_amt", "merchant_id", "merchant_name", "merchant_city", "merchant_zip",
    "card_num", "orig_ts", "proc_ts", "processed_flag"
]

daily_tran_df = spark.createDataFrame(daily_tran_data, daily_tran_schema)

daily_tran_df.write.format("delta").mode("append").saveAsTable("daily_transactions")

print(f"Loaded {len(daily_tran_data)} records into daily_transactions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Display Loaded Data Summary

# COMMAND ----------

print("\n" + "=" * 70)
print("SAMPLE DATA LOAD COMPLETE")
print("=" * 70)

# Show daily transactions with expected outcomes
print("\nDaily Transactions Loaded:")
print("-" * 70)
spark.sql("""
    SELECT 
        tran_id,
        card_num,
        tran_amt,
        tran_desc,
        CASE 
            WHEN card_num = '9999999999999999' THEN 'REJECT: Invalid Card (100)'
            WHEN card_num IN ('4555555555555555') THEN 'REJECT: Overlimit (102)'
            WHEN card_num = '4333333333333333' THEN 'REJECT: Expired (103)'
            ELSE 'VALID: Will be posted'
        END as expected_outcome
    FROM daily_transactions
    ORDER BY tran_id
""").show(truncate=False)

# COMMAND ----------

# Summary counts
print("\nData Summary:")
print("-" * 40)
print(f"Card Cross-References: {spark.sql('SELECT COUNT(*) FROM card_xref').collect()[0][0]}")
print(f"Accounts:              {spark.sql('SELECT COUNT(*) FROM accounts').collect()[0][0]}")
print(f"Category Balances:     {spark.sql('SELECT COUNT(*) FROM transaction_category_balance').collect()[0][0]}")
print(f"Daily Transactions:    {spark.sql('SELECT COUNT(*) FROM daily_transactions').collect()[0][0]}")
print(f"Posted Transactions:   {spark.sql('SELECT COUNT(*) FROM transactions').collect()[0][0]}")
print(f"Rejected Transactions: {spark.sql('SELECT COUNT(*) FROM daily_rejects').collect()[0][0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Expected Results After Running CBTRN02C
# MAGIC 
# MAGIC After running the transaction posting program:
# MAGIC - **7 transactions** should be posted successfully
# MAGIC - **3 transactions** should be rejected:
# MAGIC   - TRN20260204004: Error 100 - Invalid card number
# MAGIC   - TRN20260204005: Error 102 - Overlimit transaction
# MAGIC   - TRN20260204006: Error 103 - Expired account

print("\n" + "=" * 70)
print("EXPECTED RESULTS AFTER RUNNING CBTRN02C:")
print("=" * 70)
print("Valid transactions to be posted:    7")
print("Rejected transactions:              3")
print("  - Error 100 (Invalid Card):       1")
print("  - Error 102 (Overlimit):          1")
print("  - Error 103 (Expired Account):    1")
print("=" * 70)
