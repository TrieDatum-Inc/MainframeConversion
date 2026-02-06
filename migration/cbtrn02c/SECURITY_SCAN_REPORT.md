# CBTRN02C PySpark Migration - Security & Vulnerability Scan Report

**Scan Date:** 2026-02-06
**Scanned Files:** `cbtrn02c_post_daily_transactions.py`, `01_ddl_setup.sql`, `02_sample_data.sql`
**Tools Used:** Bandit 1.9.3 (Python SAST), Safety 3.7.0 (dependency CVE scanner), manual code review

---

## 1. Automated Scan Results

### 1.1 Bandit (Static Application Security Testing)

| Metric | Value |
|---|---|
| Lines of Code Scanned | 291 |
| Severity HIGH | 0 |
| Severity MEDIUM | 0 |
| Severity LOW | 0 |
| Total Issues | **0** |

Bandit scanned for: hardcoded passwords, shell injection, SQL injection via string formatting, insecure deserialization, weak cryptography, debug/assert misuse, and 60+ additional security checks.

### 1.2 Safety (Dependency Vulnerability Scanner)

| Package | Version | Known CVEs |
|---|---|---|
| pyspark | 3.5.4 | 0 |
| delta-spark | 3.2.1 | 0 |

No known vulnerabilities in the direct dependencies.

---

## 2. Manual Security Review

### 2.1 SQL Injection Analysis

| ID | Finding | Severity | Status |
|---|---|---|---|
| SQL-01 | Schema name used via f-string interpolation in table references | LOW | Informational |

**Details:** The `SCHEMA` variable (line 46) is used in f-strings to construct table names:
```python
SCHEMA = "carddemo"
spark.table(f"{SCHEMA}.daily_transaction")
DeltaTable.forName(spark, f"{SCHEMA}.account")
posted.write.format("delta").mode("append").saveAsTable(f"{SCHEMA}.transaction")
```

**Assessment:** `SCHEMA` is a module-level constant, not derived from user input. All table references use the Spark DataFrame API (`spark.table()`, `DeltaTable.forName()`, `.saveAsTable()`), not raw SQL string execution. The Delta MERGE conditions (lines 246, 281-284) use parameterized column references, not string concatenation of values. **No SQL injection risk.**

**Recommendation:** If `SCHEMA` is ever made configurable (e.g., via environment variable or CLI argument), validate it against an allowlist pattern (`^[a-zA-Z_][a-zA-Z0-9_]*$`) to prevent catalog traversal.

---

### 2.2 Authentication & Authorization

| ID | Finding | Severity | Status |
|---|---|---|---|
| AUTH-01 | No explicit authentication or access control in the pipeline | MEDIUM | By Design |

**Details:** The pipeline relies entirely on the Spark session's authentication context (Databricks Unity Catalog, cluster IAM role, or personal access token). It does not implement its own authentication layer.

**Assessment:** This is expected for a Databricks batch job. The Spark session inherits permissions from the cluster/workspace configuration. Access to the `carddemo` schema and its tables is governed by Unity Catalog grants or legacy table ACLs.

**Recommendation:**
- Ensure the service principal or user running this job has **minimum required grants**: `SELECT` on input tables, `INSERT`/`UPDATE` on output tables.
- Use Unity Catalog to restrict access: `GRANT SELECT ON carddemo.daily_transaction TO batch_service_principal`.
- Avoid running with admin/owner privileges.

---

### 2.3 Sensitive Data Handling

| ID | Finding | Severity | Status |
|---|---|---|---|
| DATA-01 | Card numbers stored and processed in plaintext | HIGH | Requires Action |
| DATA-02 | Account IDs and balances logged to stdout | MEDIUM | Requires Action |

**DATA-01 Details:** The `dalytran_card_num` / `tran_card_num` / `xref_card_num` fields contain full 16-digit card numbers (e.g., `'4111111111111111'` in sample data). These are stored in plaintext in Delta tables and transmitted across Spark executors during joins and shuffles.

**Assessment:** Full card numbers are PCI-DSS regulated data (PAN - Primary Account Number). Storing them in plaintext violates PCI-DSS Requirement 3.4 (render PAN unreadable anywhere it is stored). This is inherited from the original COBOL design where VSAM files contained plaintext card numbers.

**Recommendations:**
- **Tokenization:** Replace card numbers with tokens at ingestion. Use a tokenization service (e.g., AWS Payment Cryptography, Databricks column-level encryption) so the pipeline processes tokens, not real PANs.
- **Column-level encryption:** If tokenization is not feasible, use Databricks column-level encryption for `*_card_num` columns.
- **Masking:** At minimum, apply dynamic data masking in Unity Catalog: `ALTER TABLE carddemo.transaction ALTER COLUMN tran_card_num SET MASK mask_card_number;`
- **In transit:** Ensure Spark `spark.ssl.enabled=true` and cluster-to-cluster encryption is enabled.

**DATA-02 Details:** The `main()` function prints transaction counts to stdout (lines 322, 332-333, 352-353). While counts themselves are not sensitive, if logging is extended to include transaction details or error messages with card numbers, this would leak PCI data to logs.

**Recommendations:**
- Never log card numbers, even in error/debug messages.
- Use structured logging (e.g., `logging` module) instead of `print()` for production.
- Configure log redaction patterns for card number formats (`\b\d{13,19}\b`).

---

### 2.4 Input Validation

| ID | Finding | Severity | Status |
|---|---|---|---|
| INPUT-01 | No input validation on daily transaction records | MEDIUM | Requires Action |
| INPUT-02 | No data type coercion or boundary checks on amounts | LOW | Informational |

**INPUT-01 Details:** The pipeline reads `daily_transaction` records and processes them without validating:
- Card number format (should be 13-19 digits, Luhn-valid)
- Transaction amount boundaries (no check for unreasonably large amounts)
- Timestamp format (assumes `YYYY-MM-DD-HH.mm.ss.SSSSSS`)
- Required field nullability (relies on Delta table constraints)

**Assessment:** The original COBOL program also performed minimal input validation beyond the 4 business rules. However, in a cloud environment, the attack surface is broader since input data may come from multiple sources.

**Recommendations:**
- Add a pre-validation step to reject malformed records before business logic.
- Validate card number format: `F.col("dalytran_card_num").rlike("^\\d{16}$")`.
- Add amount bounds: reject transactions where `abs(dalytran_amt) > MAX_TRANSACTION_LIMIT`.
- Validate timestamp format to prevent date comparison errors.

---

### 2.5 Data Integrity & Race Conditions

| ID | Finding | Severity | Status |
|---|---|---|---|
| INTEG-01 | No idempotency protection on `post_transactions` | MEDIUM | Requires Action |
| INTEG-02 | No transaction-level atomicity across multiple table writes | MEDIUM | Informational |
| INTEG-03 | No duplicate transaction detection | LOW | Informational |

**INTEG-01 Details:** `post_transactions()` uses `.mode("append")` (line 213). If the job is re-run on the same daily data (e.g., after a failure), duplicate transaction records will be created in `carddemo.transaction`.

**Recommendations:**
- Use Delta MERGE instead of append for `post_transactions`, matching on `tran_id`.
- Or implement a "processed" flag on `daily_transaction` to prevent reprocessing.
- Or use a separate audit/control table to track which daily batches have been processed.

**INTEG-02 Details:** The pipeline writes to 4 tables sequentially (`daily_rejects`, `transaction`, `account`, `tran_cat_balance`). If the job fails mid-way (e.g., after posting transactions but before updating account balances), the data will be inconsistent.

**Recommendations:**
- Implement a compensation/rollback mechanism using Delta time travel: `RESTORE TABLE carddemo.transaction TO VERSION AS OF <pre-run-version>`.
- Or wrap all writes in a single multi-table transaction if supported by Unity Catalog.
- Log the Delta table versions before each run for recovery.

---

### 2.6 Denial of Service / Resource Exhaustion

| ID | Finding | Severity | Status |
|---|---|---|---|
| DOS-01 | No input volume limit | LOW | Informational |
| DOS-02 | `.cache()` on unbounded DataFrames | LOW | Informational |

**DOS-01 Details:** The pipeline processes all records in `daily_transaction` without any volume limits. A maliciously large input (or upstream data pipeline error) could exhaust cluster resources.

**DOS-02 Details:** `valid.cache()` and `rejects.cache()` (lines 326-327) cache the entire validated dataset in executor memory. For very large inputs, this could cause OOM errors.

**Recommendations:**
- Add a sanity check: if `daily_tran.count() > EXPECTED_MAX_DAILY_VOLUME`, log a warning or abort.
- Consider using `.persist(StorageLevel.MEMORY_AND_DISK)` instead of `.cache()` to spill to disk under memory pressure.

---

### 2.7 Credential & Secret Exposure

| ID | Finding | Severity | Status |
|---|---|---|---|
| CRED-01 | No hardcoded credentials found | N/A | Pass |

**Assessment:** The code contains no hardcoded passwords, API keys, connection strings, or tokens. Spark session creation relies on the Databricks environment configuration. No `.env` files, config files, or secret references are present.

---

### 2.8 Code Quality Security Concerns

| ID | Finding | Severity | Status |
|---|---|---|---|
| CODE-01 | Global mutable state via `SCHEMA` variable | LOW | Informational |
| CODE-02 | No error handling or logging framework | LOW | Informational |

**CODE-01 Details:** The `SCHEMA` module-level variable is modified by test code (`mod.SCHEMA = TEST_SCHEMA`). While harmless in the current context, mutable global state can lead to unintended side effects in multi-threaded or concurrent environments.

**Recommendations:** Accept `SCHEMA` as a function parameter or use an immutable configuration object.

**CODE-02 Details:** The pipeline uses `print()` for all output and has no structured error handling. Exceptions from Spark operations (e.g., `DeltaTable.forName()` on a missing table) propagate unhandled.

**Recommendations:**
- Replace `print()` with Python `logging` module configured for the Databricks log4j integration.
- Add try/except blocks around critical operations with meaningful error messages.
- Set up alerting on job failures via Databricks workflows.

---

## 3. SQL File Review (`01_ddl_setup.sql`, `02_sample_data.sql`)

| ID | Finding | Severity | Status |
|---|---|---|---|
| DDL-01 | Sample data contains realistic-looking card numbers | LOW | Informational |
| DDL-02 | No row-level security or column masking in DDL | MEDIUM | Requires Action |
| DDL-03 | No table-level permissions defined in DDL | MEDIUM | Requires Action |

**DDL-01:** The sample data uses card numbers like `4111111111111111` (standard Visa test number). These should not be replaced with real card numbers in production loading scripts.

**DDL-02:** The DDL creates tables without Unity Catalog row/column-level security policies. Add masking functions for PCI columns.

**DDL-03:** No `GRANT` statements are included. Production deployment should include explicit permission grants following least-privilege principles.

---

## 4. Summary

| Category | HIGH | MEDIUM | LOW | Informational | Total |
|---|---|---|---|---|---|
| SQL Injection | 0 | 0 | 1 | 0 | 1 |
| Authentication | 0 | 1 | 0 | 0 | 1 |
| Sensitive Data | 1 | 1 | 0 | 0 | 2 |
| Input Validation | 0 | 1 | 1 | 0 | 2 |
| Data Integrity | 0 | 2 | 1 | 0 | 3 |
| Denial of Service | 0 | 0 | 2 | 0 | 2 |
| Credentials | 0 | 0 | 0 | 0 | 0 |
| Code Quality | 0 | 0 | 2 | 0 | 2 |
| SQL/DDL Files | 0 | 2 | 1 | 0 | 3 |
| **Total** | **1** | **7** | **8** | **0** | **16** |

### Priority Actions

1. **HIGH - DATA-01:** Implement tokenization or encryption for card numbers (PCI-DSS compliance)
2. **MEDIUM - INTEG-01:** Add idempotency protection to prevent duplicate transaction posting
3. **MEDIUM - INPUT-01:** Add input validation for card number format and amount boundaries
4. **MEDIUM - DDL-02/DDL-03:** Add Unity Catalog column masking and table grants to DDL
5. **MEDIUM - AUTH-01:** Document required service principal grants for least-privilege access
6. **MEDIUM - DATA-02:** Replace `print()` with structured logging; never log card numbers
7. **MEDIUM - INTEG-02:** Implement rollback/recovery using Delta time travel
