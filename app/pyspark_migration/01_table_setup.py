# Databricks notebook source
# MAGIC %md
# MAGIC # CardDemo Delta Table Setup
# MAGIC This script creates all Delta tables required for the CBTRN02C transaction posting program.
# MAGIC 
# MAGIC ## Tables Created:
# MAGIC - daily_transactions: Input transactions to be posted
# MAGIC - card_xref: Card to account cross-reference
# MAGIC - accounts: Account master with balances
# MAGIC - transaction_category_balance: Running balances by category
# MAGIC - transactions: Posted transaction master
# MAGIC - daily_rejects: Rejected transactions with failure reasons

# COMMAND ----------

from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType, 
    IntegerType, DateType, TimestampType
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Database/Schema name - change this to your preferred location
DATABASE_NAME = "carddemo"

# Create database if not exists
spark.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
spark.sql(f"USE {DATABASE_NAME}")

print(f"Using database: {DATABASE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table 1: daily_transactions
# MAGIC Input file containing daily transactions to be posted (equivalent to DALYTRAN)

# COMMAND ----------

# Drop table if exists for clean setup
spark.sql("DROP TABLE IF EXISTS daily_transactions")

# Create daily_transactions table
# Matches CVTRA06Y.cpy structure (350 bytes in COBOL)
spark.sql("""
CREATE TABLE daily_transactions (
    tran_id STRING NOT NULL,
    tran_type_cd STRING NOT NULL,
    tran_cat_cd INT NOT NULL,
    tran_source STRING,
    tran_desc STRING,
    tran_amt DECIMAL(11,2) NOT NULL,
    merchant_id BIGINT,
    merchant_name STRING,
    merchant_city STRING,
    merchant_zip STRING,
    card_num STRING NOT NULL,
    orig_ts TIMESTAMP NOT NULL,
    proc_ts TIMESTAMP,
    processed_flag STRING DEFAULT 'N'
)
USING DELTA
COMMENT 'Daily transactions to be posted - equivalent to DALYTRAN file'
""")

print("Created table: daily_transactions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table 2: card_xref
# MAGIC Card to Account/Customer cross-reference (equivalent to XREFFILE/CARDXREF)

# COMMAND ----------

spark.sql("DROP TABLE IF EXISTS card_xref")

# Create card_xref table
# Matches CVACT03Y.cpy structure (50 bytes in COBOL)
spark.sql("""
CREATE TABLE card_xref (
    card_num STRING NOT NULL,
    cust_id BIGINT NOT NULL,
    acct_id BIGINT NOT NULL
)
USING DELTA
COMMENT 'Card to Account/Customer cross-reference - equivalent to CARDXREF file'
""")

# Add constraint for primary key behavior
spark.sql("""
ALTER TABLE card_xref 
ADD CONSTRAINT card_xref_pk PRIMARY KEY (card_num)
""")

print("Created table: card_xref")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table 3: accounts
# MAGIC Account master with balances and limits (equivalent to ACCTFILE)

# COMMAND ----------

spark.sql("DROP TABLE IF EXISTS accounts")

# Create accounts table
# Matches CVACT01Y.cpy structure (300 bytes in COBOL)
spark.sql("""
CREATE TABLE accounts (
    acct_id BIGINT NOT NULL,
    acct_active_status STRING DEFAULT 'Y',
    acct_curr_bal DECIMAL(12,2) DEFAULT 0.00,
    acct_credit_limit DECIMAL(12,2) NOT NULL,
    acct_cash_credit_limit DECIMAL(12,2),
    acct_open_date DATE,
    acct_expiration_date DATE NOT NULL,
    acct_reissue_date DATE,
    acct_curr_cyc_credit DECIMAL(12,2) DEFAULT 0.00,
    acct_curr_cyc_debit DECIMAL(12,2) DEFAULT 0.00,
    acct_addr_zip STRING,
    acct_group_id STRING
)
USING DELTA
COMMENT 'Account master with balances - equivalent to ACCTFILE'
""")

spark.sql("""
ALTER TABLE accounts 
ADD CONSTRAINT accounts_pk PRIMARY KEY (acct_id)
""")

print("Created table: accounts")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table 4: transaction_category_balance
# MAGIC Running balances by account and transaction category (equivalent to TCATBALF)

# COMMAND ----------

spark.sql("DROP TABLE IF EXISTS transaction_category_balance")

# Create transaction_category_balance table
# Matches CVTRA01Y.cpy structure (50 bytes in COBOL)
# Composite key: acct_id + tran_type_cd + tran_cat_cd
spark.sql("""
CREATE TABLE transaction_category_balance (
    acct_id BIGINT NOT NULL,
    tran_type_cd STRING NOT NULL,
    tran_cat_cd INT NOT NULL,
    tran_cat_bal DECIMAL(11,2) DEFAULT 0.00
)
USING DELTA
COMMENT 'Transaction category balance - equivalent to TCATBALF file'
""")

spark.sql("""
ALTER TABLE transaction_category_balance 
ADD CONSTRAINT tcatbal_pk PRIMARY KEY (acct_id, tran_type_cd, tran_cat_cd)
""")

print("Created table: transaction_category_balance")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table 5: transactions
# MAGIC Posted transaction master (equivalent to TRANFILE/TRANSACT)

# COMMAND ----------

spark.sql("DROP TABLE IF EXISTS transactions")

# Create transactions table
# Matches CVTRA05Y.cpy structure (350 bytes in COBOL)
spark.sql("""
CREATE TABLE transactions (
    tran_id STRING NOT NULL,
    tran_type_cd STRING NOT NULL,
    tran_cat_cd INT NOT NULL,
    tran_source STRING,
    tran_desc STRING,
    tran_amt DECIMAL(11,2) NOT NULL,
    merchant_id BIGINT,
    merchant_name STRING,
    merchant_city STRING,
    merchant_zip STRING,
    card_num STRING NOT NULL,
    orig_ts TIMESTAMP NOT NULL,
    proc_ts TIMESTAMP NOT NULL
)
USING DELTA
COMMENT 'Posted transaction master - equivalent to TRANSACT file'
""")

spark.sql("""
ALTER TABLE transactions 
ADD CONSTRAINT transactions_pk PRIMARY KEY (tran_id)
""")

print("Created table: transactions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table 6: daily_rejects
# MAGIC Rejected transactions with failure reasons (equivalent to DALYREJS)

# COMMAND ----------

spark.sql("DROP TABLE IF EXISTS daily_rejects")

# Create daily_rejects table
# Contains original transaction data plus validation failure info
spark.sql("""
CREATE TABLE daily_rejects (
    reject_id BIGINT GENERATED ALWAYS AS IDENTITY,
    tran_id STRING NOT NULL,
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
    orig_ts TIMESTAMP,
    validation_fail_reason INT NOT NULL,
    validation_fail_reason_desc STRING NOT NULL,
    reject_ts TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
COMMENT 'Rejected transactions with failure reasons - equivalent to DALYREJS file'
""")

print("Created table: daily_rejects")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Table Creation

# COMMAND ----------

# List all tables in the database
print(f"\nTables in {DATABASE_NAME} database:")
print("=" * 50)

tables = spark.sql(f"SHOW TABLES IN {DATABASE_NAME}").collect()
for table in tables:
    print(f"  - {table.tableName}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Display Table Schemas

# COMMAND ----------

table_names = [
    "daily_transactions",
    "card_xref", 
    "accounts",
    "transaction_category_balance",
    "transactions",
    "daily_rejects"
]

for table_name in table_names:
    print(f"\n{'=' * 60}")
    print(f"Schema for {table_name}:")
    print("=" * 60)
    spark.sql(f"DESCRIBE TABLE {table_name}").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup Complete
# MAGIC All Delta tables have been created successfully. 
# MAGIC Run `02_sample_data_load.py` next to load sample data.

print("\n" + "=" * 60)
print("TABLE SETUP COMPLETE")
print("=" * 60)
print(f"Database: {DATABASE_NAME}")
print("Tables created: 6")
print("  1. daily_transactions - Input transactions")
print("  2. card_xref - Card cross-reference")
print("  3. accounts - Account master")
print("  4. transaction_category_balance - Category balances")
print("  5. transactions - Posted transactions")
print("  6. daily_rejects - Rejected transactions")
print("=" * 60)
