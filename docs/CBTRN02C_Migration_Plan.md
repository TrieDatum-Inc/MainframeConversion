# CBTRN02C Migration Plan
## Mainframe COBOL to PySpark/Databricks Delta Lake

**Document Version:** 1.0  
**Date:** January 2026  
**Program:** CBTRN02C.cbl (Post Daily Transactions)  
**Target Platform:** Databricks with Delta Lake  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Source System Analysis](#2-source-system-analysis)
3. [Target Architecture](#3-target-architecture)
4. [Migration Phases](#4-migration-phases)
5. [Detailed Migration Steps](#5-detailed-migration-steps)
6. [Data Migration](#6-data-migration)
7. [Code Conversion](#7-code-conversion)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment Plan](#9-deployment-plan)
10. [Rollback Strategy](#10-rollback-strategy)
11. [Appendices](#11-appendices)

---

## 1. Executive Summary

### 1.1 Purpose
This document provides a comprehensive migration plan for converting the mainframe COBOL batch program CBTRN02C (Post Daily Transactions) to a PySpark application running on Databricks with Delta Lake as the data store.

### 1.2 Scope
The migration covers:
- COBOL program logic conversion to PySpark
- VSAM file migration to Delta Lake tables
- JCL job conversion to Databricks Jobs/Airflow DAG
- Validation and testing to ensure functional equivalence

### 1.3 Program Overview
CBTRN02C is a batch program that:
- Reads daily transaction records from a sequential file (DALYTRAN)
- Validates each transaction against reference data
- Posts valid transactions to the transaction master file
- Updates account balances and category balances
- Writes rejected transactions to a reject file with reason codes

### 1.4 Key Success Criteria
- 100% functional equivalence with mainframe program
- All validation logic produces identical results
- Reject reason codes match exactly (100, 101, 102, 103)
- Account balance updates are mathematically identical
- Performance meets or exceeds mainframe batch window

---

## 2. Source System Analysis

### 2.1 Program Inventory

| Component | Name | Type | Description |
|-----------|------|------|-------------|
| Program | CBTRN02C.cbl | COBOL Batch | Main transaction posting program |
| JCL | POSTTRAN.jcl | Job Control | Batch job definition |
| Copybook | CVTRA06Y.cpy | Data Structure | Daily transaction record (350 bytes) |
| Copybook | CVTRA05Y.cpy | Data Structure | Transaction master record (350 bytes) |
| Copybook | CVACT01Y.cpy | Data Structure | Account record (300 bytes) |
| Copybook | CVACT03Y.cpy | Data Structure | Card cross-reference (50 bytes) |
| Copybook | CVTRA01Y.cpy | Data Structure | Transaction category balance (50 bytes) |

### 2.2 File Inventory

| DD Name | Dataset Name | Type | Access | Description |
|---------|--------------|------|--------|-------------|
| DALYTRAN | AWS.M2.CARDDEMO.DALYTRAN | Sequential | Input | Daily transactions |
| TRANFILE | AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | VSAM KSDS | Output | Transaction master |
| XREFFILE | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | VSAM KSDS | Input | Card cross-reference |
| ACCTFILE | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | VSAM KSDS | I-O | Account master |
| TCATBALF | AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS | VSAM KSDS | I-O | Category balances |
| DALYREJS | AWS.M2.CARDDEMO.DALYREJS | Sequential | Output | Rejected transactions |

### 2.3 Business Logic Analysis

#### 2.3.1 Validation Rules

| Step | Validation | Reject Code | Description |
|------|------------|-------------|-------------|
| 1 | Card Lookup | 100 | Card number must exist in XREFFILE |
| 2 | Account Lookup | 101 | Account from XREF must exist in ACCTFILE |
| 3 | Overlimit Check | 102 | New balance must not exceed credit limit |
| 4 | Expiration Check | 103 | Transaction date must be before account expiration |

#### 2.3.2 Overlimit Calculation Formula
```
WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL THEN VALID ELSE REJECT(102)
```

#### 2.3.3 Account Update Logic
```
ACCT-CURR-BAL = ACCT-CURR-BAL + DALYTRAN-AMT
IF DALYTRAN-AMT >= 0 THEN
    ACCT-CURR-CYC-CREDIT = ACCT-CURR-CYC-CREDIT + DALYTRAN-AMT
ELSE
    ACCT-CURR-CYC-DEBIT = ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
```

### 2.4 Processing Characteristics

| Characteristic | Value | Impact on Migration |
|----------------|-------|---------------------|
| Processing Mode | Sequential | Must preserve order for same-account transactions |
| Record Count | ~100,000/day | Moderate volume, single partition sufficient |
| Batch Window | 2 hours | Target: < 30 minutes on Databricks |
| Error Handling | Abend on I/O error | Implement equivalent exception handling |
| Return Code | 0=Success, 4=Rejects exist | Map to job exit status |

---

## 3. Target Architecture

### 3.1 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Compute | Databricks Runtime | PySpark execution environment |
| Storage | Delta Lake | ACID-compliant data lake storage |
| Catalog | Unity Catalog | Metadata management and governance |
| Orchestration | Airflow / Databricks Workflows | Job scheduling |
| Monitoring | Databricks Jobs UI / CloudWatch | Execution monitoring |

### 3.2 Delta Lake Table Design

#### 3.2.1 Catalog and Schema Structure
```
carddemo (catalog)
├── bronze (schema) - Raw data landing zone
│   └── dalytran - Daily transaction input
├── silver (schema) - Validated and cleansed data
│   ├── transactions - Transaction master
│   ├── accounts - Account master
│   ├── card_xref - Card cross-reference
│   ├── tran_cat_balance - Category balances
│   └── transaction_rejects - Rejected transactions
└── gold (schema) - Business aggregates (future)
```

#### 3.2.2 Table Schemas

**bronze.dalytran**
```sql
CREATE TABLE carddemo.bronze.dalytran (
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
    batch_id STRING,
    ingestion_ts TIMESTAMP
)
USING DELTA
PARTITIONED BY (batch_id);
```

**silver.transactions**
```sql
CREATE TABLE carddemo.silver.transactions (
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
USING DELTA;
```

**silver.accounts**
```sql
CREATE TABLE carddemo.silver.accounts (
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
    last_updated TIMESTAMP
)
USING DELTA;
```

### 3.3 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATABRICKS ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │  Mainframe   │     │   Landing    │     │      Bronze Layer        │ │
│  │   DALYTRAN   │────►│    Zone      │────►│   bronze.dalytran        │ │
│  │  (EBCDIC)    │     │  (S3/ADLS)   │     │   (Delta Table)          │ │
│  └──────────────┘     └──────────────┘     └───────────┬──────────────┘ │
│                                                        │                 │
│                                                        ▼                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    CBTRN02C PySpark Job                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │   │
│  │  │   Read      │  │  Validate   │  │   Post      │               │   │
│  │  │  DALYTRAN   │─►│  Against    │─►│  Valid      │               │   │
│  │  │             │  │  XREF/ACCT  │  │  Trans      │               │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                           │                    │                         │
│              ┌────────────┴────────────┐       │                         │
│              ▼                         ▼       ▼                         │
│  ┌──────────────────┐    ┌──────────────────────────────────────────┐   │
│  │  Silver Layer    │    │           Silver Layer                   │   │
│  │  transaction_    │    │  ┌────────────┐  ┌────────────────────┐  │   │
│  │  rejects         │    │  │transactions│  │tran_cat_balance    │  │   │
│  │  (Delta Table)   │    │  │(MERGE)     │  │(MERGE)             │  │   │
│  └──────────────────┘    │  └────────────┘  └────────────────────┘  │   │
│                          │  ┌────────────┐                          │   │
│                          │  │accounts    │                          │   │
│                          │  │(MERGE)     │                          │   │
│                          │  └────────────┘                          │   │
│                          └──────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Migration Phases

### 4.1 Phase Overview

| Phase | Name | Duration | Key Deliverables |
|-------|------|----------|------------------|
| 1 | Discovery & Analysis | 1 week | This document, data mapping |
| 2 | Environment Setup | 1 week | Databricks workspace, Delta tables |
| 3 | Code Conversion | 2 weeks | PySpark job, unit tests |
| 4 | Data Migration | 1 week | Historical data load, validation |
| 5 | Integration Testing | 1 week | End-to-end testing, reconciliation |
| 6 | Parallel Run | 2 weeks | Run both systems, compare outputs |
| 7 | Cutover | 1 week | Production deployment, monitoring |

### 4.2 Phase Dependencies

```
Phase 1 ──► Phase 2 ──► Phase 3 ──┬──► Phase 5 ──► Phase 6 ──► Phase 7
                                  │
                       Phase 4 ───┘
```

---

## 5. Detailed Migration Steps

### 5.1 Phase 1: Discovery & Analysis

#### Step 1.1: Analyze COBOL Source Code
**Developer Actions:**
1. Review CBTRN02C.cbl line by line
2. Document all PERFORM paragraphs and their purposes
3. Identify all file I/O operations
4. Map COBOL data types to PySpark equivalents
5. Document all validation logic with exact conditions

**Deliverables:**
- Code analysis document
- Data type mapping table
- Validation logic specification

#### Step 1.2: Analyze Copybooks
**Developer Actions:**
1. Extract field definitions from each copybook
2. Calculate record lengths and field offsets
3. Document COBOL PIC clauses and their meanings
4. Create schema definitions for Delta tables

**Copybook to Schema Mapping:**

| COBOL PIC | Length | PySpark Type | Delta Type |
|-----------|--------|--------------|------------|
| PIC X(n) | n bytes | StringType | STRING |
| PIC 9(n) | n bytes | IntegerType/LongType | INT/BIGINT |
| PIC S9(n)V99 | n+2 bytes | DecimalType(n+2,2) | DECIMAL(n+2,2) |
| PIC S9(n) COMP | 2/4/8 bytes | IntegerType/LongType | INT/BIGINT |

#### Step 1.3: Analyze JCL
**Developer Actions:**
1. Review POSTTRAN.jcl for job steps
2. Document DD statements and file assignments
3. Identify job dependencies and scheduling
4. Map to Airflow DAG or Databricks Workflow

### 5.2 Phase 2: Environment Setup

#### Step 2.1: Create Databricks Workspace
**Developer Actions:**
1. Request Databricks workspace provisioning
2. Configure Unity Catalog access
3. Set up service principal for job execution
4. Configure cluster policies

**Configuration Checklist:**
- [ ] Workspace created
- [ ] Unity Catalog enabled
- [ ] Service principal created
- [ ] Cluster policy defined
- [ ] Network connectivity to data sources

#### Step 2.2: Create Delta Lake Tables
**Developer Actions:**
1. Create catalog: `carddemo`
2. Create schemas: `bronze`, `silver`, `gold`
3. Execute DDL for all tables
4. Set up table permissions

**SQL Script Example:**
```sql
-- Create catalog
CREATE CATALOG IF NOT EXISTS carddemo;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS carddemo.bronze;
CREATE SCHEMA IF NOT EXISTS carddemo.silver;

-- Create tables (see Section 3.2.2 for full DDL)
```

#### Step 2.3: Set Up Development Environment
**Developer Actions:**
1. Clone repository to local machine
2. Install Python dependencies (pyspark, delta-spark)
3. Configure Databricks CLI
4. Set up IDE with Databricks extension

**Requirements:**
```
pyspark>=3.4.0
delta-spark>=2.4.0
databricks-sdk>=0.12.0
pytest>=7.0.0
```

### 5.3 Phase 3: Code Conversion

#### Step 3.1: Create Schema Definitions Module
**Developer Actions:**
1. Create `schema_definitions.py`
2. Define StructType for each record layout
3. Define field position constants for EBCDIC parsing
4. Add validation for schema consistency

**Code Template:**
```python
from pyspark.sql.types import StructType, StructField, StringType, DecimalType, IntegerType

DALYTRAN_SCHEMA = StructType([
    StructField("tran_id", StringType(), False),
    StructField("tran_type_cd", StringType(), True),
    StructField("tran_cat_cd", IntegerType(), True),
    # ... additional fields
])
```

#### Step 3.2: Create EBCDIC Converter Module
**Developer Actions:**
1. Create `ebcdic_converter.py`
2. Implement EBCDIC to ASCII conversion
3. Handle signed zoned decimal (overpunch)
4. Handle packed decimal (COMP-3)
5. Create record parser for each copybook layout

**Key Functions:**
- `ebcdic_to_ascii(bytes) -> str`
- `parse_zoned_decimal(bytes, scale) -> Decimal`
- `parse_packed_decimal(bytes, scale) -> Decimal`
- `parse_dalytran_record(bytes) -> dict`

#### Step 3.3: Create Main PySpark Job
**Developer Actions:**
1. Create `post_daily_transactions.py`
2. Implement `CBTRN02CJob` class with methods:
   - `run()` - Main orchestration
   - `_read_daily_transactions()` - Read from bronze
   - `_validate_transactions()` - Apply all validations
   - `_post_transactions()` - Write to silver tables
   - `_generate_reconciliation_report()` - Output stats

**Validation Implementation:**
```python
def _validate_transactions(self, dalytran_df):
    # Step 1: Join with card_xref (validation 100)
    validated = dalytran_df.join(
        self.card_xref_df,
        dalytran_df.card_num == self.card_xref_df.card_num,
        "left"
    )
    
    # Mark invalid cards
    validated = validated.withColumn(
        "reject_code",
        F.when(F.col("xref_acct_id").isNull(), F.lit(100))
    )
    
    # Step 2: Join with accounts (validation 101)
    # ... continue for all validations
```

#### Step 3.4: Handle Sequential Processing
**Critical Requirement:**
COBOL processes transactions sequentially, updating account balances after each valid transaction. For exact matching:

**Option A: Collect and Process in Python (Small Volumes)**
```python
transactions = dalytran_df.collect()
for tran in transactions:
    # Validate against current account state
    # Update account state if valid
    # This matches COBOL's sequential processing
```

**Option B: Window Functions (Large Volumes)**
```python
# Calculate running balance per account
window = Window.partitionBy("acct_id").orderBy("seq_no")
df = df.withColumn(
    "running_balance",
    F.sum("tran_amt").over(window)
)
```

#### Step 3.5: Implement Delta Lake MERGE Operations
**Developer Actions:**
1. Use MERGE for idempotent updates
2. Implement upsert logic for accounts
3. Implement upsert logic for category balances

**MERGE Example:**
```python
from delta.tables import DeltaTable

accounts_delta = DeltaTable.forName(spark, "carddemo.silver.accounts")

accounts_delta.alias("target").merge(
    updates_df.alias("source"),
    "target.acct_id = source.acct_id"
).whenMatchedUpdate(set={
    "curr_bal": "source.new_curr_bal",
    "curr_cyc_credit": "source.new_curr_cyc_credit",
    "curr_cyc_debit": "source.new_curr_cyc_debit",
    "last_updated": "current_timestamp()"
}).execute()
```

#### Step 3.6: Create Airflow DAG
**Developer Actions:**
1. Create `airflow_dag.py`
2. Define DAG with daily schedule
3. Implement tasks for:
   - Generate batch_id
   - Check for input file
   - Ingest EBCDIC file to bronze
   - Run CBTRN02C job
   - Validate reconciliation
   - Send notifications

**DAG Structure:**
```python
with DAG(
    dag_id="carddemo_cbtrn02c_post_daily_transactions",
    schedule_interval="0 23 * * *",  # Daily at 11 PM UTC
    catchup=False
) as dag:
    
    generate_batch_id >> check_file >> ingest >> run_job >> validate >> notify
```

### 5.4 Phase 4: Data Migration

#### Step 4.1: Extract Reference Data from VSAM
**Developer Actions:**
1. Use IDCAMS REPRO to export VSAM to sequential files
2. Transfer files to cloud storage (S3/ADLS)
3. Verify file integrity (record counts, checksums)

**JCL Example:**
```jcl
//EXPORT   EXEC PGM=IDCAMS
//SYSPRINT DD SYSOUT=*
//INFILE   DD DSN=AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS,DISP=SHR
//OUTFILE  DD DSN=AWS.M2.CARDDEMO.ACCTDATA.EXPORT,
//            DISP=(NEW,CATLG),SPACE=(CYL,(10,5))
//SYSIN    DD *
  REPRO INFILE(INFILE) OUTFILE(OUTFILE)
/*
```

#### Step 4.2: Load Reference Data to Delta Tables
**Developer Actions:**
1. Create data loading notebook/script
2. Parse EBCDIC files using converter module
3. Load into silver tables
4. Validate record counts match source

**Loading Script:**
```python
# Load accounts
accounts_df = parse_ebcdic_file(
    spark, 
    "dbfs:/landing/ACCTDATA.EXPORT",
    ACCOUNT_SCHEMA,
    record_length=300
)
accounts_df.write.format("delta").mode("overwrite").saveAsTable("carddemo.silver.accounts")
```

#### Step 4.3: Validate Data Migration
**Developer Actions:**
1. Compare record counts
2. Compare key field values (sample)
3. Compare aggregate totals (balances)
4. Document any discrepancies

**Validation Queries:**
```sql
-- Count comparison
SELECT 'mainframe' as source, COUNT(*) as cnt FROM mainframe_export
UNION ALL
SELECT 'delta' as source, COUNT(*) as cnt FROM carddemo.silver.accounts;

-- Balance comparison
SELECT SUM(curr_bal) as total_balance FROM carddemo.silver.accounts;
```

### 5.5 Phase 5: Integration Testing

#### Step 5.1: Create Test Data
**Developer Actions:**
1. Use testing framework to generate test vectors
2. Create test cases for all validation scenarios
3. Load test data to bronze table

**Test Scenarios:**
| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| TC001 | Valid transaction | Posted successfully |
| TC002 | Invalid card | Rejected (code 100) |
| TC003 | Account not found | Rejected (code 101) |
| TC004 | Overlimit | Rejected (code 102) |
| TC005 | Expired account | Rejected (code 103) |
| TC006 | Multiple trans same account | Sequential processing correct |

#### Step 5.2: Execute Integration Tests
**Developer Actions:**
1. Run PySpark job with test data
2. Verify output counts match expected
3. Verify reject codes match expected
4. Verify account balance updates

**Test Execution:**
```bash
python run_tests.py --spark-only
```

#### Step 5.3: Reconciliation Testing
**Developer Actions:**
1. Compare transaction counts
2. Compare reject counts by reason code
3. Compare account balance changes
4. Document any differences

### 5.6 Phase 6: Parallel Run

#### Step 6.1: Set Up Parallel Execution
**Developer Actions:**
1. Configure both mainframe and Databricks jobs to run
2. Use same input file for both systems
3. Capture outputs from both systems

#### Step 6.2: Daily Reconciliation
**Developer Actions:**
1. Compare transaction counts daily
2. Compare reject counts by reason code
3. Compare account balance totals
4. Investigate any discrepancies

**Reconciliation Report Template:**
```
Date: YYYY-MM-DD
Batch ID: YYYYMMDDHHMMSS

                    Mainframe    Databricks    Difference
Transactions Read:      XXXX         XXXX           0
Transactions Posted:    XXXX         XXXX           0
Transactions Rejected:  XXXX         XXXX           0
  - Code 100:           XXXX         XXXX           0
  - Code 101:           XXXX         XXXX           0
  - Code 102:           XXXX         XXXX           0
  - Code 103:           XXXX         XXXX           0

Status: MATCH / MISMATCH
```

#### Step 6.3: Issue Resolution
**Developer Actions:**
1. Investigate any mismatches
2. Root cause analysis
3. Fix and retest
4. Document resolution

### 5.7 Phase 7: Cutover

#### Step 7.1: Pre-Cutover Checklist
- [ ] All parallel run days matched
- [ ] Performance meets requirements
- [ ] Monitoring and alerting configured
- [ ] Runbook documented
- [ ] Rollback procedure tested
- [ ] Stakeholder sign-off obtained

#### Step 7.2: Cutover Execution
**Developer Actions:**
1. Disable mainframe job
2. Enable Databricks job as primary
3. Monitor first production run
4. Verify outputs

#### Step 7.3: Post-Cutover Validation
**Developer Actions:**
1. Verify job completed successfully
2. Verify downstream systems received data
3. Verify no alerts triggered
4. Document cutover completion

---

## 6. Data Migration

### 6.1 Data Mapping

#### 6.1.1 DALYTRAN Record Mapping

| COBOL Field | Offset | Length | PIC | Delta Column | Delta Type |
|-------------|--------|--------|-----|--------------|------------|
| DALYTRAN-ID | 0 | 16 | X(16) | tran_id | STRING |
| DALYTRAN-TYPE-CD | 16 | 2 | X(02) | tran_type_cd | STRING |
| DALYTRAN-CAT-CD | 18 | 4 | 9(04) | tran_cat_cd | INT |
| DALYTRAN-SOURCE | 22 | 10 | X(10) | tran_source | STRING |
| DALYTRAN-DESC | 32 | 100 | X(100) | tran_desc | STRING |
| DALYTRAN-AMT | 132 | 11 | S9(09)V99 | tran_amt | DECIMAL(11,2) |
| DALYTRAN-MERCHANT-ID | 143 | 9 | 9(09) | merchant_id | BIGINT |
| DALYTRAN-MERCHANT-NAME | 152 | 50 | X(50) | merchant_name | STRING |
| DALYTRAN-MERCHANT-CITY | 202 | 50 | X(50) | merchant_city | STRING |
| DALYTRAN-MERCHANT-ZIP | 252 | 10 | X(10) | merchant_zip | STRING |
| DALYTRAN-CARD-NUM | 262 | 16 | X(16) | card_num | STRING |
| DALYTRAN-ORIG-TS | 278 | 26 | X(26) | orig_ts | STRING |
| DALYTRAN-PROC-TS | 304 | 26 | X(26) | proc_ts | STRING |
| FILLER | 330 | 20 | X(20) | - | - |

### 6.2 EBCDIC Conversion

#### 6.2.1 Character Data (PIC X)
- Use code page cp037 (US EBCDIC) or cp1047 (Open Systems)
- Convert bytes to ASCII string
- Trim trailing spaces

#### 6.2.2 Unsigned Numeric (PIC 9)
- Each byte represents one digit
- EBCDIC digits: 0xF0-0xF9 = '0'-'9'
- Convert to integer

#### 6.2.3 Signed Zoned Decimal (PIC S9)
- Sign is in zone nibble of last byte
- Positive: 0xC or 0xF in zone
- Negative: 0xD in zone
- Overpunch characters: {=+0, A-I=+1-9, }=-0, J-R=-1-9

#### 6.2.4 Packed Decimal (COMP-3)
- Two digits per byte (except last)
- Last nibble is sign (C=+, D=-)
- Example: +12345 = 0x12345C

---

## 7. Code Conversion

### 7.1 COBOL to PySpark Mapping

| COBOL Construct | PySpark Equivalent |
|-----------------|-------------------|
| PERFORM paragraph | Function call |
| PERFORM UNTIL | while loop or DataFrame operations |
| READ file | spark.read or DataFrame.collect() |
| WRITE record | DataFrame.write or DeltaTable.merge |
| REWRITE record | DeltaTable.merge with whenMatchedUpdate |
| IF condition | F.when() or Python if |
| MOVE field TO field | F.col() or withColumn |
| ADD value TO field | F.col() + value |
| COMPUTE | Arithmetic expression |
| STRING concatenation | F.concat() |

### 7.2 Key Code Sections

#### 7.2.1 Main Processing Loop
**COBOL:**
```cobol
PERFORM UNTIL END-OF-FILE = 'Y'
    PERFORM 1000-DALYTRAN-GET-NEXT
    IF END-OF-FILE = 'N'
        PERFORM 1500-VALIDATE-TRAN
        IF WS-VALIDATION-FAIL-REASON = 0
            PERFORM 2000-POST-TRANSACTION
        ELSE
            PERFORM 2500-WRITE-REJECT-REC
        END-IF
    END-IF
END-PERFORM
```

**PySpark:**
```python
def run(self):
    dalytran_df = self._read_daily_transactions()
    valid_df, rejects_df = self._validate_transactions(dalytran_df)
    self._post_transactions(valid_df)
    self._write_rejects(rejects_df)
    return self._generate_reconciliation_report()
```

#### 7.2.2 Validation Logic
**COBOL:**
```cobol
1500-A-LOOKUP-XREF.
    MOVE DALYTRAN-CARD-NUM TO FD-XREF-CARD-NUM
    READ XREF-FILE INTO CARD-XREF-RECORD
       INVALID KEY
         MOVE 100 TO WS-VALIDATION-FAIL-REASON
         MOVE 'INVALID CARD NUMBER FOUND'
           TO WS-VALIDATION-FAIL-REASON-DESC
    END-READ.
```

**PySpark:**
```python
# Join with card_xref
validated = dalytran_df.join(
    card_xref_df,
    dalytran_df.card_num == card_xref_df.card_num,
    "left"
).withColumn(
    "reject_code",
    F.when(F.col("xref_acct_id").isNull(), F.lit(100))
).withColumn(
    "reject_desc",
    F.when(F.col("reject_code") == 100, F.lit("INVALID CARD NUMBER FOUND"))
)
```

---

## 8. Testing Strategy

### 8.1 Test Levels

| Level | Scope | Responsibility | Tools |
|-------|-------|----------------|-------|
| Unit | Individual functions | Developer | pytest |
| Integration | End-to-end job | Developer | Testing framework |
| System | Full pipeline | QA | Databricks Jobs |
| UAT | Business validation | Business | Production-like data |
| Parallel | Mainframe comparison | Developer + QA | Reconciliation scripts |

### 8.2 Test Data Strategy

#### 8.2.1 Golden Dataset
- Deterministic test data covering all scenarios
- Generated by testing framework
- Version controlled

#### 8.2.2 Production Sample
- Anonymized subset of production data
- Used for performance testing
- Refreshed periodically

### 8.3 Acceptance Criteria

| Criterion | Threshold | Measurement |
|-----------|-----------|-------------|
| Functional equivalence | 100% | All test cases pass |
| Reject code accuracy | 100% | Codes match mainframe |
| Balance accuracy | 100% | Totals match to cent |
| Performance | < 30 min | Job duration |
| Availability | 99.9% | Job success rate |

---

## 9. Deployment Plan

### 9.1 Deployment Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| PySpark job | /databricks-migration/cbtrn02c/ | Main job code |
| Schema definitions | /databricks-migration/cbtrn02c/ | Table schemas |
| EBCDIC converter | /databricks-migration/cbtrn02c/ | Data conversion |
| Airflow DAG | /airflow/dags/ | Job orchestration |
| DDL scripts | /databricks-migration/ddl/ | Table creation |

### 9.2 Deployment Steps

1. **Deploy DDL** - Create/update Delta tables
2. **Deploy Code** - Upload PySpark modules to Databricks
3. **Configure Job** - Create Databricks job definition
4. **Deploy DAG** - Upload Airflow DAG
5. **Enable Monitoring** - Configure alerts
6. **Validate** - Run smoke test

### 9.3 Environment Promotion

```
DEV ──► TEST ──► UAT ──► PROD
```

---

## 10. Rollback Strategy

### 10.1 Rollback Triggers
- Job failure rate > 5%
- Data quality issues detected
- Downstream system failures
- Business stakeholder request

### 10.2 Rollback Procedure

1. **Disable Databricks job**
2. **Re-enable mainframe job**
3. **Restore Delta tables** (if needed)
   ```sql
   RESTORE TABLE carddemo.silver.accounts TO VERSION AS OF <version>;
   ```
4. **Notify stakeholders**
5. **Root cause analysis**

### 10.3 Data Recovery
Delta Lake provides time travel for data recovery:
```sql
-- View table history
DESCRIBE HISTORY carddemo.silver.accounts;

-- Restore to specific version
RESTORE TABLE carddemo.silver.accounts TO VERSION AS OF 5;

-- Restore to specific timestamp
RESTORE TABLE carddemo.silver.accounts TO TIMESTAMP AS OF '2026-01-15 10:00:00';
```

---

## 11. Appendices

### 11.1 Glossary

| Term | Definition |
|------|------------|
| COBOL | Common Business-Oriented Language |
| VSAM | Virtual Storage Access Method |
| KSDS | Key-Sequenced Data Set |
| Delta Lake | Open-source storage layer for data lakes |
| Unity Catalog | Databricks metadata management service |
| EBCDIC | Extended Binary Coded Decimal Interchange Code |
| Overpunch | Sign representation in zoned decimal |

### 11.2 Reference Documents

- CardDemo Application README
- COBOL Copybook Reference (CVTRA05Y, CVTRA06Y, CVACT01Y, CVACT03Y, CVTRA01Y)
- Databricks Delta Lake Documentation
- PySpark API Reference

### 11.3 Contact Information

| Role | Name | Email |
|------|------|-------|
| Project Lead | TBD | TBD |
| Technical Lead | TBD | TBD |
| Mainframe SME | TBD | TBD |
| Databricks Admin | TBD | TBD |

### 11.4 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Devin | Initial version |

---

**End of Document**
