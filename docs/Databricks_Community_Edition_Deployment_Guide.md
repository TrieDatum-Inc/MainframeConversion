# Deploying CBTRN02C to Databricks Community Edition

A step-by-step guide for deploying the migrated CBTRN02C PySpark code to Databricks Community Edition (free version).

---

## Prerequisites

- Email address for signup
- Web browser
- The migration code files (from `databricks-migration/cbtrn02c/` folder)

---

## Step 1: Sign Up for Databricks Community Edition

**What is Databricks Community Edition?**
Databricks Community Edition is a free, limited version of Databricks that provides a single-node Apache Spark cluster. It's perfect for learning and POC work.

**How to sign up:**

1. Go to: https://community.cloud.databricks.com/login.html

2. Click **"Sign Up"** (not the enterprise trial)

3. Fill in your details:
   - First Name
   - Last Name
   - Email
   - Company (can be "Personal" or your company name)

4. Select **"Community Edition"** when asked (NOT the 14-day trial)

5. Verify your email and complete registration

6. Once logged in, you'll see the Databricks workspace with a left sidebar showing: Workspace, Repos, Data, Compute, etc.

---

## Step 2: Create a Compute Cluster

**What is a Cluster?**
A cluster is the Spark engine that runs your code. Nothing runs until you start a cluster.

**Steps:**

1. In the left sidebar, click **"Compute"** (or "Clusters" in older UI)

2. Click **"Create Cluster"** button

3. Configure the cluster:
   - **Cluster Name:** `cbtrn02c-poc`
   - **Databricks Runtime Version:** Select the latest LTS version (e.g., `13.3 LTS` or `14.3 LTS`)
   - Leave other settings as default (Community Edition has limited options)

4. Click **"Create Cluster"**

5. Wait for the cluster to start (green circle = running). This takes 3-5 minutes.

**Important Notes:**
- Community Edition clusters auto-terminate after 2 hours of inactivity
- You can restart the cluster anytime from the Compute page
- Only one cluster can run at a time in Community Edition

---

## Step 3: Create a Workspace Folder

**What is the Workspace?**
The Workspace is where you store notebooks and files. Think of it like a file system.

**Steps:**

1. In the left sidebar, click **"Workspace"**

2. Click on your username (or Users → your email)

3. Right-click and select **"Create" → "Folder"**

4. Name it: `cbtrn02c_migration`

5. Click **"Create"**

---

## Step 4: Create the Main Notebook

**What is a Notebook?**
A notebook is an interactive document where you write and run code in cells. This is how you'll run the migration code.

**Steps:**

1. Inside your `cbtrn02c_migration` folder, right-click and select **"Create" → "Notebook"**

2. Configure:
   - **Name:** `CBTRN02C_Setup_and_Run`
   - **Default Language:** Python
   - **Cluster:** Select `cbtrn02c-poc`

3. Click **"Create"**

---

## Step 5: Create the Database and Tables

**Important: Community Edition Limitation**
Community Edition does NOT have Unity Catalog. Instead of `catalog.schema.table` naming, we use simple `database.table` naming.

**Copy and paste this code into your notebook, one cell at a time:**

### Cell 1: Create Database
```python
# Create the carddemo database
# In Community Edition, we use a simple database instead of Unity Catalog
spark.sql("CREATE DATABASE IF NOT EXISTS carddemo")
spark.sql("USE carddemo")
print("Database 'carddemo' created and selected")
```

**Run the cell:** Click the cell and press `Shift+Enter` or click the play button

### Cell 2: Create Daily Transactions Table (Bronze)
```python
# Create bronze layer table for daily transaction input
spark.sql("""
    CREATE TABLE IF NOT EXISTS carddemo.dalytran (
        tran_id STRING,
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
        orig_ts STRING,
        proc_ts STRING,
        batch_id STRING,
        ingestion_ts TIMESTAMP
    )
    USING DELTA
""")
print("Table 'carddemo.dalytran' created")
```

### Cell 3: Create Transactions Table (Silver)
```python
# Create silver layer table for posted transactions
spark.sql("""
    CREATE TABLE IF NOT EXISTS carddemo.transactions (
        tran_id STRING,
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
        orig_ts STRING,
        proc_ts STRING,
        batch_id STRING,
        created_ts TIMESTAMP
    )
    USING DELTA
""")
print("Table 'carddemo.transactions' created")
```

### Cell 4: Create Accounts Table
```python
# Create accounts table (replaces VSAM ACCTFILE)
spark.sql("""
    CREATE TABLE IF NOT EXISTS carddemo.accounts (
        acct_id STRING,
        active_status STRING,
        curr_bal DECIMAL(12,2),
        credit_limit DECIMAL(12,2),
        cash_credit_limit DECIMAL(12,2),
        open_date STRING,
        expiration_date STRING,
        reissue_date STRING,
        curr_cyc_credit DECIMAL(12,2),
        curr_cyc_debit DECIMAL(12,2),
        addr_zip STRING,
        group_id STRING,
        last_updated_ts TIMESTAMP,
        last_updated_batch_id STRING
    )
    USING DELTA
""")
print("Table 'carddemo.accounts' created")
```

### Cell 5: Create Card Cross-Reference Table
```python
# Create card cross-reference table (replaces VSAM XREFFILE)
spark.sql("""
    CREATE TABLE IF NOT EXISTS carddemo.card_xref (
        card_num STRING,
        cust_id STRING,
        acct_id STRING
    )
    USING DELTA
""")
print("Table 'carddemo.card_xref' created")
```

### Cell 6: Create Transaction Category Balance Table
```python
# Create transaction category balance table (replaces VSAM TCATBALF)
spark.sql("""
    CREATE TABLE IF NOT EXISTS carddemo.tran_cat_balance (
        acct_id STRING,
        tran_type_cd STRING,
        tran_cat_cd INT,
        tran_cat_bal DECIMAL(11,2),
        last_updated_ts TIMESTAMP,
        last_updated_batch_id STRING
    )
    USING DELTA
""")
print("Table 'carddemo.tran_cat_balance' created")
```

### Cell 7: Create Rejects Table
```python
# Create rejects table (replaces DALYREJS)
spark.sql("""
    CREATE TABLE IF NOT EXISTS carddemo.transaction_rejects (
        tran_id STRING,
        card_num STRING,
        tran_amt DECIMAL(11,2),
        orig_ts STRING,
        reject_reason_code INT,
        reject_reason_desc STRING,
        batch_id STRING,
        rejected_ts TIMESTAMP
    )
    USING DELTA
""")
print("Table 'carddemo.transaction_rejects' created")
```

---

## Step 6: Load Sample Data

### Cell 8: Load Sample Accounts
```python
from pyspark.sql.functions import current_timestamp, lit

# Sample accounts data
sample_accounts = [
    ("00000000001", "Y", 1500.75, 10000.00, 2000.00, "2020-01-15", "2027-12-31", None, 500.00, -200.00, "10001", "PREMIUM"),
    ("00000000002", "Y", 3250.50, 15000.00, 3000.00, "2019-06-20", "2028-06-30", None, 1000.00, -500.00, "20002", "GOLD"),
    ("00000000003", "N", 0.00, 5000.00, 1000.00, "2018-03-10", "2024-03-31", None, 0.00, 0.00, "30003", "STANDARD"),
    ("00000000004", "Y", 7890.25, 25000.00, 5000.00, "2021-09-01", "2029-09-30", None, 2500.00, -1000.00, "40004", "PLATINUM"),
    ("00000000005", "Y", 450.00, 3000.00, 500.00, "2022-02-14", "2030-02-28", None, 100.00, -50.00, "50005", "STANDARD"),
]

accounts_df = spark.createDataFrame(
    sample_accounts,
    ["acct_id", "active_status", "curr_bal", "credit_limit", "cash_credit_limit",
     "open_date", "expiration_date", "reissue_date", "curr_cyc_credit", "curr_cyc_debit",
     "addr_zip", "group_id"]
).withColumn("last_updated_ts", current_timestamp()) \
 .withColumn("last_updated_batch_id", lit("INITIAL_LOAD"))

accounts_df.write.format("delta").mode("overwrite").saveAsTable("carddemo.accounts")
print(f"Loaded {accounts_df.count()} sample accounts")
accounts_df.show()
```

### Cell 9: Load Sample Card Cross-References
```python
# Sample card cross-references
sample_xrefs = [
    ("4111111111111111", "100000001", "00000000001"),
    ("4222222222222222", "100000002", "00000000002"),
    ("4333333333333333", "100000003", "00000000003"),
    ("4444444444444444", "100000004", "00000000004"),
    ("4555555555555555", "100000005", "00000000005"),
]

xref_df = spark.createDataFrame(sample_xrefs, ["card_num", "cust_id", "acct_id"])
xref_df.write.format("delta").mode("overwrite").saveAsTable("carddemo.card_xref")
print(f"Loaded {xref_df.count()} sample card cross-references")
xref_df.show()
```

### Cell 10: Load Sample Daily Transactions
```python
from pyspark.sql.functions import current_timestamp

# Sample daily transactions (some valid, some will be rejected)
sample_dalytran = [
    # Valid transaction - will be posted
    ("TRN0000000000001", "PR", 1001, "POS", "GROCERY STORE PURCHASE", -45.67, 123456789, "WHOLE FOODS", "NEW YORK", "10001", "4111111111111111", "2026-01-15-10.30.00.000000", None, "20260115120000"),
    # Valid transaction - will be posted
    ("TRN0000000000002", "PR", 1002, "ONLINE", "AMAZON PURCHASE", -129.99, 987654321, "AMAZON.COM", "SEATTLE", "98101", "4222222222222222", "2026-01-15-11.45.00.000000", None, "20260115120000"),
    # Valid credit/payment - will be posted
    ("TRN0000000000003", "CR", 2001, "PAYMENT", "PAYMENT RECEIVED", 500.00, 0, "CUSTOMER PAYMENT", "N/A", "00000", "4111111111111111", "2026-01-15-14.00.00.000000", None, "20260115120000"),
    # INVALID CARD - will be rejected with code 100
    ("TRN0000000000004", "PR", 1001, "POS", "GAS STATION", -55.00, 111222333, "SHELL", "CHICAGO", "60601", "9999999999999999", "2026-01-15-09.00.00.000000", None, "20260115120000"),
    # OVERLIMIT - will be rejected with code 102
    ("TRN0000000000005", "PR", 1003, "POS", "ELECTRONICS", -15000.00, 444555666, "BEST BUY", "LOS ANGELES", "90001", "4444444444444444", "2026-01-15-16.30.00.000000", None, "20260115120000"),
]

dalytran_df = spark.createDataFrame(
    sample_dalytran,
    ["tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc", "tran_amt",
     "merchant_id", "merchant_name", "merchant_city", "merchant_zip", "card_num",
     "orig_ts", "proc_ts", "batch_id"]
).withColumn("ingestion_ts", current_timestamp())

dalytran_df.write.format("delta").mode("overwrite").saveAsTable("carddemo.dalytran")
print(f"Loaded {dalytran_df.count()} sample daily transactions")
dalytran_df.show(truncate=False)
```

---

## Step 7: Run the CBTRN02C Job

Now we'll run the actual transaction posting logic that replicates the mainframe COBOL program.

### Cell 11: Define Validation Constants
```python
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

print("Validation constants defined")
```

### Cell 12: Run the Transaction Posting Job
```python
from pyspark.sql import functions as F
from delta.tables import DeltaTable
from datetime import datetime

# Configuration
BATCH_ID = "20260115120000"  # Must match the batch_id in dalytran table

print("=" * 60)
print("CBTRN02C - POST DAILY TRANSACTIONS - STARTING")
print("=" * 60)

# Step 1: Read daily transactions
dalytran_df = spark.table("carddemo.dalytran").filter(F.col("batch_id") == BATCH_ID)
records_read = dalytran_df.count()
print(f"Records read from DALYTRAN: {records_read}")

# Step 2: Load reference tables
xref_df = spark.table("carddemo.card_xref")
accounts_df = spark.table("carddemo.accounts")

# Step 3: Validate transactions
# Join with card_xref to get account ID
validated_df = dalytran_df.alias("t").join(
    xref_df.alias("x"),
    F.col("t.card_num") == F.col("x.card_num"),
    "left"
).select(
    "t.*",
    F.col("x.acct_id").alias("xref_acct_id"),
    F.col("x.cust_id").alias("xref_cust_id")
)

# Validation 1: Card number exists
validated_df = validated_df.withColumn(
    "validation_1_pass",
    F.col("xref_acct_id").isNotNull()
).withColumn(
    "reject_reason_1",
    F.when(~F.col("validation_1_pass"), F.lit(REASON_INVALID_CARD))
)

# Join with accounts
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

# Validation 2: Account exists
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

# Validation 3: Overlimit check
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

# Validation 4: Expiration check
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

# Determine final status
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

# Split valid and rejected
valid_df = validated_df.filter(F.col("is_valid") == True)
rejects_df = validated_df.filter(F.col("is_valid") == False)

valid_count = valid_df.count()
reject_count = rejects_df.count()
print(f"Valid transactions: {valid_count}")
print(f"Rejected transactions: {reject_count}")

# Step 4: Post valid transactions
proc_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")[:26]

tran_records = valid_df.select(
    "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
    "tran_amt", "merchant_id", "merchant_name", "merchant_city",
    "merchant_zip", "card_num", "orig_ts", "batch_id"
).withColumn("proc_ts", F.lit(proc_ts)) \
 .withColumn("created_ts", F.current_timestamp())

# Write to transactions table
tran_records.write.format("delta").mode("append").saveAsTable("carddemo.transactions")
print(f"Posted {valid_count} transactions to carddemo.transactions")

# Step 5: Write rejects
if reject_count > 0:
    reject_records = rejects_df.select(
        "tran_id", "card_num", "tran_amt", "orig_ts", "reject_reason_code", "batch_id"
    ).withColumn(
        "reject_reason_desc",
        F.when(F.col("reject_reason_code") == 100, F.lit("INVALID CARD NUMBER FOUND"))
         .when(F.col("reject_reason_code") == 101, F.lit("ACCOUNT RECORD NOT FOUND"))
         .when(F.col("reject_reason_code") == 102, F.lit("OVERLIMIT TRANSACTION"))
         .when(F.col("reject_reason_code") == 103, F.lit("TRANSACTION RECEIVED AFTER ACCT EXPIRATION"))
    ).withColumn("rejected_ts", F.current_timestamp())
    
    reject_records.write.format("delta").mode("append").saveAsTable("carddemo.transaction_rejects")
    print(f"Wrote {reject_count} rejects to carddemo.transaction_rejects")

print("=" * 60)
print("CBTRN02C - POST DAILY TRANSACTIONS - COMPLETED")
print("=" * 60)
```

---

## Step 8: Verify Results

### Cell 13: Check Posted Transactions
```sql
%sql
-- View posted transactions
SELECT * FROM carddemo.transactions
```

### Cell 14: Check Rejected Transactions
```sql
%sql
-- View rejected transactions with reason codes
SELECT 
    tran_id,
    card_num,
    tran_amt,
    reject_reason_code,
    reject_reason_desc
FROM carddemo.transaction_rejects
```

### Cell 15: Check Account Balances
```sql
%sql
-- View current account balances
SELECT 
    acct_id,
    active_status,
    curr_bal,
    credit_limit,
    curr_cyc_credit,
    curr_cyc_debit
FROM carddemo.accounts
```

### Cell 16: Summary Statistics
```sql
%sql
-- Reconciliation report
SELECT 
    'Transactions Read' as metric, COUNT(*) as count FROM carddemo.dalytran WHERE batch_id = '20260115120000'
UNION ALL
SELECT 'Transactions Posted', COUNT(*) FROM carddemo.transactions
UNION ALL
SELECT 'Transactions Rejected', COUNT(*) FROM carddemo.transaction_rejects
UNION ALL
SELECT 'Reject Code 100 (Invalid Card)', COUNT(*) FROM carddemo.transaction_rejects WHERE reject_reason_code = 100
UNION ALL
SELECT 'Reject Code 102 (Overlimit)', COUNT(*) FROM carddemo.transaction_rejects WHERE reject_reason_code = 102
```

---

## Expected Results

After running all cells, you should see:

| Metric | Count |
|--------|-------|
| Transactions Read | 5 |
| Transactions Posted | 3 |
| Transactions Rejected | 2 |
| Reject Code 100 (Invalid Card) | 1 |
| Reject Code 102 (Overlimit) | 1 |

**Posted Transactions:**
- TRN0000000000001: Grocery purchase (-$45.67)
- TRN0000000000002: Amazon purchase (-$129.99)
- TRN0000000000003: Payment received (+$500.00)

**Rejected Transactions:**
- TRN0000000000004: Invalid card (code 100) - card 9999999999999999 not in card_xref
- TRN0000000000005: Overlimit (code 102) - $15,000 exceeds credit limit

---

## Troubleshooting

### "Table not found" error
- Make sure you ran the CREATE TABLE cells first
- Check that you're using `carddemo.tablename` (not `carddemo.silver.tablename`)

### Cluster not responding
- Go to Compute and check if cluster is running (green circle)
- If terminated, click "Start" to restart it

### "Delta" format not recognized
- Make sure you're using Databricks Runtime 7.0 or later
- Delta Lake is built into Databricks Runtime

### Data not showing
- Run the cells in order (create tables → load data → run job)
- Check the batch_id matches between dalytran and the job

---

## Community Edition Limitations

1. **No Unity Catalog** - We use simple `database.table` naming instead of `catalog.schema.table`
2. **Single cluster** - Only one cluster can run at a time
3. **Auto-termination** - Clusters stop after 2 hours of inactivity
4. **No scheduling** - Cannot schedule jobs; must run manually from notebooks
5. **Limited storage** - Small storage quota for DBFS
6. **No Airflow integration** - The Airflow DAG from the migration POC won't work here

---

## Next Steps

Once you've verified the POC works:

1. **Production Databricks**: Upgrade to paid Databricks for Unity Catalog, job scheduling, and larger clusters
2. **Real Data**: Replace sample data with actual mainframe data (converted from EBCDIC)
3. **Airflow Integration**: Set up Airflow to orchestrate the job on a schedule
4. **Monitoring**: Add logging and alerting for production runs

---

## Files Reference

The full migration code is in the repository under `databricks-migration/cbtrn02c/`:
- `post_daily_transactions.py` - Full PySpark job class (for production use)
- `setup_delta_tables.py` - Table creation script (for Unity Catalog environments)
- `ebcdic_converter.py` - EBCDIC to ASCII conversion utilities
- `airflow_dag.py` - Airflow DAG for scheduling (for production use)
- `schema_definitions.py` - PySpark schema definitions
