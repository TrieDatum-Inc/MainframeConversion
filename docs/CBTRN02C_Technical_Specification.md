# CBTRN02C - Post Daily Transactions - Technical Specification

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| **Program Name** | CBTRN02C |
| **Program Type** | Batch COBOL |
| **Application** | CardDemo |
| **Function** | Post daily credit card transactions to master files |
| **Lines of Code** | 732 |
| **Execution Frequency** | Daily (typically end-of-day) |

## 2. Business Logic

### 2.1 Purpose
CBTRN02C is the core daily transaction posting program for the CardDemo credit card system. It reads pending transactions from the daily transaction file, validates each transaction against business rules, and posts valid transactions to the transaction master while updating account balances. Invalid transactions are written to a reject file with reason codes for manual review or reprocessing.

### 2.2 Processing Flow

1. **Read** daily transaction record from DALYTRAN
2. **Validate** transaction against 4 business rules (see Section 5)
3. **If Valid:**
   - Update transaction category balance (TCATBALF)
   - Update account balance (ACCTFILE)
   - Write transaction to transaction master (TRANFILE)
4. **If Invalid:**
   - Write to reject file (DALYREJS) with reason code
5. **Repeat** until end of file
6. **Report** transaction count and reject count

### 2.3 Key Business Rules

- Transactions must have a valid card number linked to an account
- Account must exist in the account master
- Transaction must not cause account to exceed credit limit
- Transaction must not be dated after account expiration
- Account balances are updated in real-time as transactions are posted
- Positive amounts = credits (payments), Negative amounts = debits (purchases)

---

## 3. Input Files

### 3.1 DALYTRAN - Daily Transaction File (INPUT)

| Attribute | Value |
|-----------|-------|
| **DD Name** | DALYTRAN |
| **Dataset** | AWS.M2.CARDDEMO.DALYTRAN.PS |
| **Organization** | Sequential (PS) |
| **Record Length** | 350 bytes |
| **Access Mode** | Sequential |
| **Copybook** | CVTRA06Y.cpy |

**Record Layout (DALYTRAN-RECORD):**

| Field | PIC | Bytes | Offset | Description |
|-------|-----|-------|--------|-------------|
| DALYTRAN-ID | X(16) | 16 | 0 | Transaction ID (unique) |
| DALYTRAN-TYPE-CD | X(02) | 2 | 16 | Transaction type (PR=Purchase, CR=Credit, etc.) |
| DALYTRAN-CAT-CD | 9(04) | 4 | 18 | Transaction category code |
| DALYTRAN-SOURCE | X(10) | 10 | 22 | Source system (POS, ONLINE, ATM, etc.) |
| DALYTRAN-DESC | X(100) | 100 | 32 | Transaction description |
| DALYTRAN-AMT | S9(09)V99 | 11 | 132 | Amount (signed, 2 decimals) |
| DALYTRAN-MERCHANT-ID | 9(09) | 9 | 143 | Merchant identifier |
| DALYTRAN-MERCHANT-NAME | X(50) | 50 | 152 | Merchant name |
| DALYTRAN-MERCHANT-CITY | X(50) | 50 | 202 | Merchant city |
| DALYTRAN-MERCHANT-ZIP | X(10) | 10 | 252 | Merchant ZIP code |
| DALYTRAN-CARD-NUM | X(16) | 16 | 262 | Card number |
| DALYTRAN-ORIG-TS | X(26) | 26 | 278 | Original timestamp |
| DALYTRAN-PROC-TS | X(26) | 26 | 304 | Processed timestamp |
| FILLER | X(20) | 20 | 330 | Reserved |

---

### 3.2 XREFFILE - Card Cross-Reference File (INPUT)

| Attribute | Value |
|-----------|-------|
| **DD Name** | XREFFILE |
| **Dataset** | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS |
| **Organization** | VSAM KSDS (Indexed) |
| **Record Length** | 50 bytes |
| **Key** | XREF-CARD-NUM (16 bytes, offset 0) |
| **Access Mode** | Random |
| **Copybook** | CVACT03Y.cpy |

**Record Layout (CARD-XREF-RECORD):**

| Field | PIC | Bytes | Description |
|-------|-----|-------|-------------|
| XREF-CARD-NUM | X(16) | 16 | Card number (PRIMARY KEY) |
| XREF-CUST-ID | 9(09) | 9 | Customer ID |
| XREF-ACCT-ID | 9(11) | 11 | Account ID |
| FILLER | X(14) | 14 | Reserved |

---

### 3.3 ACCTFILE - Account Master File (INPUT/OUTPUT)

| Attribute | Value |
|-----------|-------|
| **DD Name** | ACCTFILE |
| **Dataset** | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS |
| **Organization** | VSAM KSDS (Indexed) |
| **Record Length** | 300 bytes |
| **Key** | ACCT-ID (11 bytes, offset 0) |
| **Access Mode** | Random (I-O) |
| **Copybook** | CVACT01Y.cpy |

**Record Layout (ACCOUNT-RECORD):**

| Field | PIC | Bytes | Description |
|-------|-----|-------|-------------|
| ACCT-ID | 9(11) | 11 | Account ID (PRIMARY KEY) |
| ACCT-ACTIVE-STATUS | X(01) | 1 | Active status (Y/N) |
| ACCT-CURR-BAL | S9(10)V99 | 12 | Current balance |
| ACCT-CREDIT-LIMIT | S9(10)V99 | 12 | Credit limit |
| ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | 12 | Cash credit limit |
| ACCT-OPEN-DATE | X(10) | 10 | Account open date (YYYY-MM-DD) |
| ACCT-EXPIRAION-DATE | X(10) | 10 | Expiration date (YYYY-MM-DD) |
| ACCT-REISSUE-DATE | X(10) | 10 | Reissue date |
| ACCT-CURR-CYC-CREDIT | S9(10)V99 | 12 | Current cycle credits |
| ACCT-CURR-CYC-DEBIT | S9(10)V99 | 12 | Current cycle debits |
| ACCT-ADDR-ZIP | X(10) | 10 | ZIP code |
| ACCT-GROUP-ID | X(10) | 10 | Account group ID |
| FILLER | X(178) | 178 | Reserved |

---

### 3.4 TCATBALF - Transaction Category Balance File (INPUT/OUTPUT)

| Attribute | Value |
|-----------|-------|
| **DD Name** | TCATBALF |
| **Dataset** | AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS |
| **Organization** | VSAM KSDS (Indexed) |
| **Record Length** | 50 bytes |
| **Key** | Composite (ACCT-ID + TYPE-CD + CAT-CD) = 17 bytes |
| **Access Mode** | Random (I-O) |
| **Copybook** | CVTRA01Y.cpy |

**Record Layout (TRAN-CAT-BAL-RECORD):**

| Field | PIC | Bytes | Description |
|-------|-----|-------|-------------|
| TRANCAT-ACCT-ID | 9(11) | 11 | Account ID (KEY part 1) |
| TRANCAT-TYPE-CD | X(02) | 2 | Transaction type (KEY part 2) |
| TRANCAT-CD | 9(04) | 4 | Category code (KEY part 3) |
| TRAN-CAT-BAL | S9(09)V99 | 11 | Running balance for this category |
| FILLER | X(22) | 22 | Reserved |

---

## 4. Output Files

### 4.1 TRANFILE - Transaction Master File (OUTPUT)

| Attribute | Value |
|-----------|-------|
| **DD Name** | TRANFILE |
| **Dataset** | AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS |
| **Organization** | VSAM KSDS (Indexed) |
| **Record Length** | 350 bytes |
| **Key** | TRAN-ID (16 bytes, offset 0) |
| **Access Mode** | Random (OUTPUT) |
| **Copybook** | CVTRA05Y.cpy |

**Record Layout (TRAN-RECORD):**

| Field | PIC | Bytes | Description |
|-------|-----|-------|-------------|
| TRAN-ID | X(16) | 16 | Transaction ID (PRIMARY KEY) |
| TRAN-TYPE-CD | X(02) | 2 | Transaction type |
| TRAN-CAT-CD | 9(04) | 4 | Category code |
| TRAN-SOURCE | X(10) | 10 | Source system |
| TRAN-DESC | X(100) | 100 | Description |
| TRAN-AMT | S9(09)V99 | 11 | Amount |
| TRAN-MERCHANT-ID | 9(09) | 9 | Merchant ID |
| TRAN-MERCHANT-NAME | X(50) | 50 | Merchant name |
| TRAN-MERCHANT-CITY | X(50) | 50 | Merchant city |
| TRAN-MERCHANT-ZIP | X(10) | 10 | Merchant ZIP |
| TRAN-CARD-NUM | X(16) | 16 | Card number |
| TRAN-ORIG-TS | X(26) | 26 | Original timestamp |
| TRAN-PROC-TS | X(26) | 26 | Processed timestamp (set by program) |
| FILLER | X(20) | 20 | Reserved |

---

### 4.2 DALYREJS - Daily Rejects File (OUTPUT)

| Attribute | Value |
|-----------|-------|
| **DD Name** | DALYREJS |
| **Dataset** | AWS.M2.CARDDEMO.DALYREJS(+1) |
| **Organization** | Sequential (GDG - Generation Data Group) |
| **Record Length** | 430 bytes |
| **Record Format** | Fixed (RECFM=F) |
| **Access Mode** | Sequential (OUTPUT) |

**Record Layout (REJECT-RECORD):**

| Field | Bytes | Description |
|-------|-------|-------------|
| REJECT-TRAN-DATA | 350 | Original transaction record |
| VALIDATION-TRAILER | 80 | Validation failure information |

**Validation Trailer Layout:**

| Field | PIC | Bytes | Description |
|-------|-----|-------|-------------|
| WS-VALIDATION-FAIL-REASON | 9(04) | 4 | Reject reason code |
| WS-VALIDATION-FAIL-REASON-DESC | X(76) | 76 | Reject reason description |

---

## 5. Validation Rules

CBTRN02C performs 4 sequential validation checks. If any check fails, the transaction is rejected and subsequent checks are skipped.

### Validation 1: Card Number Validation (Code 100)

| Attribute | Value |
|-----------|-------|
| **Paragraph** | 1500-A-LOOKUP-XREF |
| **Reject Code** | 100 |
| **Reject Description** | "INVALID CARD NUMBER FOUND" |
| **Logic** | Read XREFFILE using DALYTRAN-CARD-NUM as key |
| **Pass Condition** | Record found (file status = '00') |
| **Fail Condition** | Record not found (INVALID KEY) |

```cobol
READ XREF-FILE INTO CARD-XREF-RECORD
   INVALID KEY
     MOVE 100 TO WS-VALIDATION-FAIL-REASON
     MOVE 'INVALID CARD NUMBER FOUND' TO WS-VALIDATION-FAIL-REASON-DESC
```

---

### Validation 2: Account Existence (Code 101)

| Attribute | Value |
|-----------|-------|
| **Paragraph** | 1500-B-LOOKUP-ACCT |
| **Reject Code** | 101 |
| **Reject Description** | "ACCOUNT RECORD NOT FOUND" |
| **Logic** | Read ACCTFILE using XREF-ACCT-ID as key |
| **Pass Condition** | Record found (file status = '00') |
| **Fail Condition** | Record not found (INVALID KEY) |

```cobol
MOVE XREF-ACCT-ID TO FD-ACCT-ID
READ ACCOUNT-FILE INTO ACCOUNT-RECORD
   INVALID KEY
     MOVE 101 TO WS-VALIDATION-FAIL-REASON
     MOVE 'ACCOUNT RECORD NOT FOUND' TO WS-VALIDATION-FAIL-REASON-DESC
```

---

### Validation 3: Credit Limit Check (Code 102)

| Attribute | Value |
|-----------|-------|
| **Paragraph** | 1500-B-LOOKUP-ACCT (continued) |
| **Reject Code** | 102 |
| **Reject Description** | "OVERLIMIT TRANSACTION" |
| **Formula** | `WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT` |
| **Pass Condition** | `ACCT-CREDIT-LIMIT >= WS-TEMP-BAL` |
| **Fail Condition** | `ACCT-CREDIT-LIMIT < WS-TEMP-BAL` |

```cobol
COMPUTE WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT
                    - ACCT-CURR-CYC-DEBIT
                    + DALYTRAN-AMT

IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL
  CONTINUE
ELSE
  MOVE 102 TO WS-VALIDATION-FAIL-REASON
  MOVE 'OVERLIMIT TRANSACTION' TO WS-VALIDATION-FAIL-REASON-DESC
END-IF
```

**Note:** This calculates the projected balance after the transaction and compares it to the credit limit. Negative transaction amounts (purchases) increase the balance owed.

---

### Validation 4: Account Expiration Check (Code 103)

| Attribute | Value |
|-----------|-------|
| **Paragraph** | 1500-B-LOOKUP-ACCT (continued) |
| **Reject Code** | 103 |
| **Reject Description** | "TRANSACTION RECEIVED AFTER ACCT EXPIRATION" |
| **Logic** | Compare transaction date to account expiration date |
| **Pass Condition** | `ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS(1:10)` |
| **Fail Condition** | Transaction date is after expiration date |

```cobol
IF ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS (1:10)
  CONTINUE
ELSE
  MOVE 103 TO WS-VALIDATION-FAIL-REASON
  MOVE 'TRANSACTION RECEIVED AFTER ACCT EXPIRATION' TO WS-VALIDATION-FAIL-REASON-DESC
END-IF
```

**Note:** Only the first 10 characters of the timestamp (YYYY-MM-DD) are compared.

---

## 6. Update Logic

### 6.1 Transaction Category Balance Update (2700-UPDATE-TCATBAL)

For each valid transaction, the program updates the running balance by account + transaction type + category:

1. Build composite key: ACCT-ID + TYPE-CD + CAT-CD
2. Read TCATBALF record
3. If record exists: `ADD DALYTRAN-AMT TO TRAN-CAT-BAL` and REWRITE
4. If record not found: Create new record with `TRAN-CAT-BAL = DALYTRAN-AMT` and WRITE

---

### 6.2 Account Balance Update (2800-UPDATE-ACCOUNT-REC)

For each valid transaction, the program updates the account master:

```cobol
ADD DALYTRAN-AMT TO ACCT-CURR-BAL
IF DALYTRAN-AMT >= 0
   ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT
ELSE
   ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT
END-IF
REWRITE FD-ACCTFILE-REC FROM ACCOUNT-RECORD
```

- **Positive amounts** (payments/credits): Added to ACCT-CURR-CYC-CREDIT
- **Negative amounts** (purchases/debits): Added to ACCT-CURR-CYC-DEBIT
- **ACCT-CURR-BAL**: Always updated with the transaction amount

---

### 6.3 Transaction Write (2900-WRITE-TRANSACTION-FILE)

The validated transaction is written to TRANFILE with:
- All fields copied from DALYTRAN
- TRAN-PROC-TS set to current timestamp (DB2 format: YYYY-MM-DD-HH.MM.SS.NNNNNN)

---

## 7. JCL to Execute

```jcl
//POSTTRAN JOB 'POSTTRAN',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID
//*******************************************************************
//* Process and load daily transaction file and create transaction
//* category balance and update transaction master vsam
//*******************************************************************
//STEP15 EXEC PGM=CBTRN02C
//STEPLIB  DD DISP=SHR,
//            DSN=AWS.M2.CARDDEMO.LOADLIB
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//TRANFILE DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS
//DALYTRAN DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.DALYTRAN.PS
//XREFFILE DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS
//DALYREJS DD DISP=(NEW,CATLG,DELETE),
//         UNIT=SYSDA,
//         DCB=(RECFM=F,LRECL=430,BLKSIZE=0),
//         SPACE=(CYL,(1,1),RLSE),
//         DSN=AWS.M2.CARDDEMO.DALYREJS(+1)
//ACCTFILE DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS
//TCATBALF DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS
```

**JCL Explanation:**

| DD Name | Purpose | Disposition |
|---------|---------|-------------|
| STEPLIB | Load library containing CBTRN02C executable | SHR (shared) |
| SYSPRINT | Program output messages | SYSOUT (print) |
| SYSOUT | Additional output | SYSOUT (print) |
| TRANFILE | Transaction master VSAM file | SHR (read/write) |
| DALYTRAN | Daily transaction input file | SHR (read) |
| XREFFILE | Card cross-reference VSAM file | SHR (read) |
| DALYREJS | Reject output file (GDG +1 = new generation) | NEW,CATLG |
| ACCTFILE | Account master VSAM file | SHR (read/write) |
| TCATBALF | Transaction category balance VSAM file | SHR (read/write) |

---

## 8. Program Dependencies

### 8.1 Called Programs
**CBTRN02C does NOT call any other programs.** It is a self-contained batch program.

### 8.2 Copybooks Used

| Copybook | Purpose |
|----------|---------|
| CVTRA06Y.cpy | Daily transaction record layout (DALYTRAN-RECORD) |
| CVTRA05Y.cpy | Transaction master record layout (TRAN-RECORD) |
| CVACT03Y.cpy | Card cross-reference record layout (CARD-XREF-RECORD) |
| CVACT01Y.cpy | Account master record layout (ACCOUNT-RECORD) |
| CVTRA01Y.cpy | Transaction category balance layout (TRAN-CAT-BAL-RECORD) |

### 8.3 Related Programs

| Program | Relationship |
|---------|--------------|
| CBTRN01C | Simpler version - verification only, no posting |
| CBACT04C | Interest calculation - uses TCATBALF updated by CBTRN02C |
| CBSTM03A/B/C | Statement generation - uses TRANFILE written by CBTRN02C |

---

## 9. Return Codes

| Return Code | Meaning |
|-------------|---------|
| 0 | Success - all transactions processed, no rejects |
| 4 | Warning - some transactions rejected (WS-REJECT-COUNT > 0) |
| 12 | Error - file I/O error (program abends) |
| 999 | Abend - critical error |

---

## 10. Architectural Diagram

```
                            CBTRN02C - POST DAILY TRANSACTIONS
                            ===================================

    +-----------------+
    |    DALYTRAN     |     Sequential Input File
    | (Daily Trans)   |     AWS.M2.CARDDEMO.DALYTRAN.PS
    | RECLN=350       |     
    +--------+--------+
             |
             | READ (Sequential)
             v
    +--------+--------+
    |                 |
    |    CBTRN02C     |     COBOL Batch Program
    |                 |     
    |  +------------+ |
    |  | 1. READ    | |
    |  +-----+------+ |
    |        |        |
    |        v        |
    |  +------------+ |     +------------------+
    |  | 2. LOOKUP  +------>|    XREFFILE      |  VSAM KSDS (Read)
    |  |    XREF    | |     | (Card Xref)      |  Key: CARD-NUM
    |  +-----+------+ |     | RECLN=50         |
    |        |        |     +------------------+
    |        v        |
    |  +------------+ |     +------------------+
    |  | 3. LOOKUP  +------>|    ACCTFILE      |  VSAM KSDS (I-O)
    |  |    ACCT    | |     | (Account Master) |  Key: ACCT-ID
    |  +-----+------+ |     | RECLN=300        |
    |        |        |     +------------------+
    |        v        |            ^
    |  +------------+ |            |
    |  | 4. VALIDATE| |            | REWRITE (Update Balance)
    |  |  - Code 100| |            |
    |  |  - Code 101| |     +------+
    |  |  - Code 102| |     |
    |  |  - Code 103| |     |
    |  +-----+------+ |     |
    |        |        |     |
    |   VALID?        |     |
    |   /    \        |     |
    |  YES    NO      |     |
    |   |      |      |     |
    |   v      v      |     |
    |  +--+  +---+    |     |
    |  |OK|  |REJ|    |     |
    |  +-++  +-+-+    |     |
    |    |     |      |     |
    +----+-----+------+     |
         |     |            |
         |     |            |
         v     v            |
    +----+--+  +----+----+  |     +------------------+
    | POST  |  | WRITE   |  +---->|    TCATBALF      |  VSAM KSDS (I-O)
    | TRANS |  | REJECT  |        | (Category Bal)   |  Key: ACCT+TYPE+CAT
    +---+---+  +----+----+        | RECLN=50         |
        |           |             +------------------+
        |           |
        v           v
    +---+-------+   +------------+
    |  TRANFILE |   |  DALYREJS  |
    | (Trans    |   | (Rejects)  |
    |  Master)  |   | RECLN=430  |
    | RECLN=350 |   +------------+
    +-----------+   Sequential Output (GDG)
    VSAM KSDS       AWS.M2.CARDDEMO.DALYREJS(+1)
    (Write)


    ============================================================================
                              DATA FLOW SUMMARY
    ============================================================================

    INPUT FILES (Read):
    +------------------+------------------+------------------+
    |     DALYTRAN     |     XREFFILE     |     ACCTFILE     |
    |  Daily Trans     |  Card Xref       |  Account Master  |
    |  (Sequential)    |  (VSAM KSDS)     |  (VSAM KSDS)     |
    +------------------+------------------+------------------+

    OUTPUT FILES (Write):
    +------------------+------------------+------------------+
    |     TRANFILE     |     ACCTFILE     |     TCATBALF     |
    |  Trans Master    |  (Updated)       |  Category Bal    |
    |  (VSAM KSDS)     |  (VSAM KSDS)     |  (VSAM KSDS)     |
    +------------------+------------------+------------------+
    |                  DALYREJS                              |
    |              Rejected Transactions                     |
    |                (Sequential GDG)                        |
    +--------------------------------------------------------+


    ============================================================================
                           VALIDATION FLOW DIAGRAM
    ============================================================================

                    +-------------------+
                    | Read DALYTRAN     |
                    | Transaction       |
                    +---------+---------+
                              |
                              v
                    +---------+---------+
                    | Lookup Card in    |
                    | XREFFILE          |
                    +---------+---------+
                              |
                    +---------+---------+
                    | Card Found?       |
                    +---------+---------+
                       |           |
                      YES          NO
                       |           |
                       v           v
              +--------+--+    +---+--------+
              | Lookup    |    | REJECT     |
              | Account   |    | Code: 100  |
              +-----+-----+    +------------+
                    |
           +--------+---------+
           | Account Found?   |
           +--------+---------+
              |           |
             YES          NO
              |           |
              v           v
     +--------+--+    +---+--------+
     | Check     |    | REJECT     |
     | Overlimit |    | Code: 101  |
     +-----+-----+    +------------+
           |
    +------+-------+
    | Within Limit?|
    +------+-------+
       |        |
      YES       NO
       |        |
       v        v
    +--+----+  +---+--------+
    | Check |  | REJECT     |
    | Expiry|  | Code: 102  |
    +---+---+  +------------+
        |
    +---+----------+
    | Not Expired? |
    +---+----------+
       |        |
      YES       NO
       |        |
       v        v
    +--+------+  +---+--------+
    | POST    |  | REJECT     |
    | TRANS   |  | Code: 103  |
    +---------+  +------------+
```

---

## 11. Sample Console Output

```
START OF EXECUTION OF PROGRAM CBTRN02C
TCATBAL record not found for key : 00000000001PR1001.. Creating.
TCATBAL record not found for key : 00000000002PR1002.. Creating.
TRANSACTIONS PROCESSED :000000005
TRANSACTIONS REJECTED  :000000002
END OF EXECUTION OF PROGRAM CBTRN02C
```

---

## 12. Error Handling

| Error Condition | Action |
|-----------------|--------|
| File open error | Display error, show file status, ABEND with code 999 |
| File read error (not EOF) | Display error, show file status, ABEND with code 999 |
| File write error | Display error, show file status, ABEND with code 999 |
| Validation failure | Write to DALYREJS, continue processing |
| Account rewrite error | Set reason code 109, continue (non-fatal) |

---

## 13. Performance Considerations

- **Sequential read** of DALYTRAN is efficient for batch processing
- **Random access** to VSAM files (XREFFILE, ACCTFILE, TCATBALF) via indexed keys
- **Single-pass processing** - each transaction is fully processed before reading the next
- **No sorting required** - transactions can be in any order
- **GDG for rejects** - allows historical tracking of rejected transactions

---

*Document generated for CardDemo CBTRN02C migration project*
