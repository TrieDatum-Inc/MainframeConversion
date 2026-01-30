"""
File Generators for CBTRN02C Testing

This module generates the input files needed for both COBOL and Spark testing:
1. DALYTRAN - Daily transaction input file (sequential)
2. ACCTFILE - Account master file (indexed)
3. XREFFILE - Card cross-reference file (indexed)
4. TCATBALF - Transaction category balance file (indexed)

For COBOL (GnuCOBOL):
- Generates ASCII fixed-length record files
- GnuCOBOL uses environment variables to map file names

For Spark:
- Generates CSV/Parquet files that can be loaded into Delta tables
"""

import os
import struct
from decimal import Decimal
from typing import List
from pathlib import Path
import csv
import json

# Import test vector definitions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "test_data"))
from test_vectors import (
    AccountRecord, CardXrefRecord, TranCatBalRecord, 
    DailyTransaction, TestVector
)


# =============================================================================
# Record Formatting Functions (COBOL Fixed-Length Records)
# =============================================================================

def format_pic_9(value: int, length: int) -> str:
    """Format a numeric value as PIC 9(n) - unsigned numeric."""
    return str(value).zfill(length)[:length]


def format_pic_x(value: str, length: int) -> str:
    """Format a string value as PIC X(n) - alphanumeric."""
    return value.ljust(length)[:length]


def format_pic_s9v99(value: Decimal, int_digits: int, dec_digits: int = 2) -> str:
    """
    Format a signed decimal as PIC S9(n)V99 - signed numeric with implied decimal.
    For GnuCOBOL, we use trailing sign representation.
    """
    # Convert to string with proper precision
    abs_value = abs(value)
    int_part = int(abs_value)
    dec_part = int((abs_value - int_part) * (10 ** dec_digits))
    
    # Format as fixed-length string
    result = str(int_part).zfill(int_digits) + str(dec_part).zfill(dec_digits)
    
    # For negative values, we need to handle the sign
    # GnuCOBOL uses overpunch or trailing sign depending on configuration
    # For simplicity, we'll use a format that GnuCOBOL can read
    if value < 0:
        # Replace last digit with overpunch character (negative)
        last_digit = result[-1]
        overpunch_neg = {'0': '}', '1': 'J', '2': 'K', '3': 'L', '4': 'M',
                         '5': 'N', '6': 'O', '7': 'P', '8': 'Q', '9': 'R'}
        result = result[:-1] + overpunch_neg.get(last_digit, '}')
    else:
        # Positive - use overpunch for positive (or leave as-is for unsigned display)
        last_digit = result[-1]
        overpunch_pos = {'0': '{', '1': 'A', '2': 'B', '3': 'C', '4': 'D',
                         '5': 'E', '6': 'F', '7': 'G', '8': 'H', '9': 'I'}
        result = result[:-1] + overpunch_pos.get(last_digit, '{')
    
    return result


def format_pic_s9v99_display(value: Decimal, int_digits: int, dec_digits: int = 2) -> str:
    """
    Format a signed decimal as PIC S9(n)V99 - signed zoned decimal.
    The sign is embedded in the zone nibble of the last digit (overpunch).
    Total length = int_digits + dec_digits (no separate sign character).
    """
    abs_value = abs(value)
    int_part = int(abs_value)
    dec_part = int((abs_value - int_part) * (10 ** dec_digits))
    
    result = str(int_part).zfill(int_digits) + str(dec_part).zfill(dec_digits)
    
    # For GnuCOBOL compatibility, use overpunch representation
    # Negative: 0=}, 1=J, 2=K, 3=L, 4=M, 5=N, 6=O, 7=P, 8=Q, 9=R
    # Positive: 0={, 1=A, 2=B, 3=C, 4=D, 5=E, 6=F, 7=G, 8=H, 9=I
    last_digit = result[-1]
    
    if value < 0:
        overpunch = {'0': '}', '1': 'J', '2': 'K', '3': 'L', '4': 'M',
                     '5': 'N', '6': 'O', '7': 'P', '8': 'Q', '9': 'R'}
        result = result[:-1] + overpunch.get(last_digit, '}')
    else:
        overpunch = {'0': '{', '1': 'A', '2': 'B', '3': 'C', '4': 'D',
                     '5': 'E', '6': 'F', '7': 'G', '8': 'H', '9': 'I'}
        result = result[:-1] + overpunch.get(last_digit, '{')
    
    return result


# =============================================================================
# COBOL File Generators
# =============================================================================

def generate_dalytran_record(tran: DailyTransaction) -> str:
    """
    Generate a DALYTRAN record (350 bytes) based on CVTRA06Y.cpy layout.
    
    01  DALYTRAN-RECORD.
        05  DALYTRAN-ID                 PIC X(16).
        05  DALYTRAN-TYPE-CD            PIC X(02).
        05  DALYTRAN-CAT-CD             PIC 9(04).
        05  DALYTRAN-SOURCE             PIC X(10).
        05  DALYTRAN-DESC               PIC X(100).
        05  DALYTRAN-AMT                PIC S9(09)V99.  (11 digits + sign = 12)
        05  DALYTRAN-MERCHANT-ID        PIC 9(09).
        05  DALYTRAN-MERCHANT-NAME      PIC X(50).
        05  DALYTRAN-MERCHANT-CITY      PIC X(50).
        05  DALYTRAN-MERCHANT-ZIP       PIC X(10).
        05  DALYTRAN-CARD-NUM           PIC X(16).
        05  DALYTRAN-ORIG-TS            PIC X(26).
        05  DALYTRAN-PROC-TS            PIC X(26).
        05  FILLER                      PIC X(20).
    """
    record = ""
    record += format_pic_x(tran.tran_id, 16)           # DALYTRAN-ID
    record += format_pic_x(tran.type_cd, 2)            # DALYTRAN-TYPE-CD
    record += format_pic_9(tran.cat_cd, 4)             # DALYTRAN-CAT-CD
    record += format_pic_x(tran.source, 10)           # DALYTRAN-SOURCE
    record += format_pic_x(tran.desc, 100)            # DALYTRAN-DESC
    record += format_pic_s9v99_display(tran.amount, 9, 2)  # DALYTRAN-AMT (12 chars with sign)
    record += format_pic_9(tran.merchant_id, 9)       # DALYTRAN-MERCHANT-ID
    record += format_pic_x(tran.merchant_name, 50)    # DALYTRAN-MERCHANT-NAME
    record += format_pic_x(tran.merchant_city, 50)    # DALYTRAN-MERCHANT-CITY
    record += format_pic_x(tran.merchant_zip, 10)     # DALYTRAN-MERCHANT-ZIP
    record += format_pic_x(tran.card_num, 16)         # DALYTRAN-CARD-NUM
    record += format_pic_x(tran.orig_ts, 26)          # DALYTRAN-ORIG-TS
    record += format_pic_x("", 26)                    # DALYTRAN-PROC-TS (empty on input)
    record += format_pic_x("", 20)                    # FILLER
    
    # Verify record length
    assert len(record) == 350, f"DALYTRAN record length is {len(record)}, expected 350"
    
    return record


def generate_account_record(acct: AccountRecord) -> str:
    """
    Generate an ACCTFILE record (300 bytes) based on CVACT01Y.cpy layout.
    
    01  ACCOUNT-RECORD.
        05  ACCT-ID                     PIC 9(11).
        05  ACCT-ACTIVE-STATUS          PIC X(01).
        05  ACCT-CURR-BAL               PIC S9(10)V99.  (13 chars with sign)
        05  ACCT-CREDIT-LIMIT           PIC S9(10)V99.
        05  ACCT-CASH-CREDIT-LIMIT      PIC S9(10)V99.
        05  ACCT-OPEN-DATE              PIC X(10).
        05  ACCT-EXPIRAION-DATE         PIC X(10).
        05  ACCT-REISSUE-DATE           PIC X(10).
        05  ACCT-CURR-CYC-CREDIT        PIC S9(10)V99.
        05  ACCT-CURR-CYC-DEBIT         PIC S9(10)V99.
        05  ACCT-ADDR-ZIP               PIC X(10).
        05  ACCT-GROUP-ID               PIC X(10).
        05  FILLER                      PIC X(178).
    """
    record = ""
    record += format_pic_9(int(acct.acct_id), 11)     # ACCT-ID
    record += format_pic_x(acct.active_status, 1)     # ACCT-ACTIVE-STATUS
    record += format_pic_s9v99_display(acct.curr_bal, 10, 2)  # ACCT-CURR-BAL
    record += format_pic_s9v99_display(acct.credit_limit, 10, 2)  # ACCT-CREDIT-LIMIT
    record += format_pic_s9v99_display(acct.cash_credit_limit, 10, 2)  # ACCT-CASH-CREDIT-LIMIT
    record += format_pic_x(acct.open_date, 10)        # ACCT-OPEN-DATE
    record += format_pic_x(acct.expiration_date, 10)  # ACCT-EXPIRAION-DATE
    record += format_pic_x(acct.reissue_date, 10)     # ACCT-REISSUE-DATE
    record += format_pic_s9v99_display(acct.curr_cyc_credit, 10, 2)  # ACCT-CURR-CYC-CREDIT
    record += format_pic_s9v99_display(acct.curr_cyc_debit, 10, 2)   # ACCT-CURR-CYC-DEBIT
    record += format_pic_x(acct.addr_zip, 10)         # ACCT-ADDR-ZIP
    record += format_pic_x(acct.group_id, 10)         # ACCT-GROUP-ID
    record += format_pic_x("", 178)                   # FILLER
    
    # Verify record length
    assert len(record) == 300, f"ACCOUNT record length is {len(record)}, expected 300"
    
    return record


def generate_xref_record(xref: CardXrefRecord) -> str:
    """
    Generate a XREFFILE record (50 bytes) based on CVACT03Y.cpy layout.
    
    01 CARD-XREF-RECORD.
        05  XREF-CARD-NUM               PIC X(16).
        05  XREF-CUST-ID                PIC 9(09).
        05  XREF-ACCT-ID                PIC 9(11).
        05  FILLER                      PIC X(14).
    """
    record = ""
    record += format_pic_x(xref.card_num, 16)         # XREF-CARD-NUM
    record += format_pic_9(int(xref.cust_id), 9)      # XREF-CUST-ID
    record += format_pic_9(int(xref.acct_id), 11)     # XREF-ACCT-ID
    record += format_pic_x("", 14)                    # FILLER
    
    # Verify record length
    assert len(record) == 50, f"XREF record length is {len(record)}, expected 50"
    
    return record


def generate_tcatbal_record(tcatbal: TranCatBalRecord) -> str:
    """
    Generate a TCATBALF record (50 bytes) based on CVTRA01Y.cpy layout.
    
    01  TRAN-CAT-BAL-RECORD.
        05  TRAN-CAT-KEY.
           10 TRANCAT-ACCT-ID           PIC 9(11).
           10 TRANCAT-TYPE-CD           PIC X(02).
           10 TRANCAT-CD                PIC 9(04).
        05  TRAN-CAT-BAL                PIC S9(09)V99.  (12 chars with sign)
        05  FILLER                      PIC X(22).
    """
    record = ""
    record += format_pic_9(int(tcatbal.acct_id), 11)  # TRANCAT-ACCT-ID
    record += format_pic_x(tcatbal.type_cd, 2)        # TRANCAT-TYPE-CD
    record += format_pic_9(tcatbal.cat_cd, 4)         # TRANCAT-CD
    record += format_pic_s9v99_display(tcatbal.balance, 9, 2)  # TRAN-CAT-BAL
    record += format_pic_x("", 21)                    # FILLER (adjusted for sign)
    
    # Verify record length
    assert len(record) == 50, f"TCATBAL record length is {len(record)}, expected 50"
    
    return record


# =============================================================================
# File Writers
# =============================================================================

def write_cobol_sequential_file(records: List[str], filepath: str):
    """Write records to a sequential file for COBOL."""
    with open(filepath, 'w', newline='') as f:
        for record in records:
            f.write(record + '\n')


def write_cobol_indexed_file(records: List[str], filepath: str):
    """
    Write records to an indexed file for GnuCOBOL.
    GnuCOBOL can use various file formats for indexed files.
    We'll use a simple sequential format that can be loaded.
    """
    with open(filepath, 'w', newline='') as f:
        for record in records:
            f.write(record + '\n')


# =============================================================================
# CSV/Parquet Writers for Spark
# =============================================================================

def write_accounts_csv(accounts: List[AccountRecord], filepath: str):
    """Write accounts to CSV for Spark testing."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'acct_id', 'active_status', 'curr_bal', 'credit_limit', 
            'cash_credit_limit', 'open_date', 'expiration_date', 'reissue_date',
            'curr_cyc_credit', 'curr_cyc_debit', 'addr_zip', 'group_id'
        ])
        for acct in accounts:
            writer.writerow([
                acct.acct_id, acct.active_status, str(acct.curr_bal),
                str(acct.credit_limit), str(acct.cash_credit_limit),
                acct.open_date, acct.expiration_date, acct.reissue_date,
                str(acct.curr_cyc_credit), str(acct.curr_cyc_debit),
                acct.addr_zip, acct.group_id
            ])


def write_xrefs_csv(xrefs: List[CardXrefRecord], filepath: str):
    """Write card cross-references to CSV for Spark testing."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['card_num', 'cust_id', 'acct_id'])
        for xref in xrefs:
            writer.writerow([xref.card_num, xref.cust_id, xref.acct_id])


def write_transactions_csv(transactions: List[DailyTransaction], filepath: str):
    """Write daily transactions to CSV for Spark testing."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'tran_id', 'tran_type_cd', 'tran_cat_cd', 'tran_source', 'tran_desc',
            'tran_amt', 'merchant_id', 'merchant_name', 'merchant_city',
            'merchant_zip', 'card_num', 'orig_ts'
        ])
        for tran in transactions:
            writer.writerow([
                tran.tran_id, tran.type_cd, tran.cat_cd, tran.source, tran.desc,
                str(tran.amount), tran.merchant_id, tran.merchant_name,
                tran.merchant_city, tran.merchant_zip, tran.card_num, tran.orig_ts
            ])


def write_expected_results_json(test_vector: TestVector, filepath: str):
    """Write expected results to JSON for validation."""
    expected = {
        'test_name': test_vector.name,
        'description': test_vector.description,
        'expected_records_read': test_vector.expected_records_read,
        'expected_records_written': test_vector.expected_records_written,
        'expected_records_rejected': test_vector.expected_records_rejected,
        'transactions': [
            {
                'tran_id': t.tran_id,
                'expected_valid': t.expected_valid,
                'expected_reject_code': t.expected_reject_code,
                'expected_reject_desc': t.expected_reject_desc
            }
            for t in test_vector.daily_transactions
        ]
    }
    with open(filepath, 'w') as f:
        json.dump(expected, f, indent=2)


# =============================================================================
# Main Generator Function
# =============================================================================

def generate_test_files(test_vector: TestVector, output_dir: str):
    """
    Generate all test files for a given test vector.
    
    Creates:
    - cobol/DALYTRAN.dat - Daily transactions (sequential)
    - cobol/ACCTFILE.dat - Account master (indexed)
    - cobol/XREFFILE.dat - Card cross-reference (indexed)
    - cobol/TCATBALF.dat - Transaction category balance (indexed)
    - spark/accounts.csv - Accounts for Spark
    - spark/card_xref.csv - Card cross-references for Spark
    - spark/dalytran.csv - Daily transactions for Spark
    - expected/results.json - Expected results for validation
    """
    output_path = Path(output_dir)
    cobol_dir = output_path / "cobol"
    spark_dir = output_path / "spark"
    expected_dir = output_path / "expected"
    
    # Create directories
    cobol_dir.mkdir(parents=True, exist_ok=True)
    spark_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate COBOL files
    dalytran_records = [generate_dalytran_record(t) for t in test_vector.daily_transactions]
    write_cobol_sequential_file(dalytran_records, str(cobol_dir / "DALYTRAN.dat"))
    
    account_records = [generate_account_record(a) for a in test_vector.accounts]
    write_cobol_indexed_file(account_records, str(cobol_dir / "ACCTFILE.dat"))
    
    xref_records = [generate_xref_record(x) for x in test_vector.card_xrefs]
    write_cobol_indexed_file(xref_records, str(cobol_dir / "XREFFILE.dat"))
    
    tcatbal_records = [generate_tcatbal_record(t) for t in test_vector.initial_tran_cat_bal]
    write_cobol_indexed_file(tcatbal_records, str(cobol_dir / "TCATBALF.dat"))
    
    # Create empty output files for COBOL
    open(str(cobol_dir / "TRANFILE.dat"), 'w').close()
    open(str(cobol_dir / "DALYREJS.dat"), 'w').close()
    
    # Generate Spark files
    write_accounts_csv(test_vector.accounts, str(spark_dir / "accounts.csv"))
    write_xrefs_csv(test_vector.card_xrefs, str(spark_dir / "card_xref.csv"))
    write_transactions_csv(test_vector.daily_transactions, str(spark_dir / "dalytran.csv"))
    
    # Generate expected results
    write_expected_results_json(test_vector, str(expected_dir / "results.json"))
    
    print(f"Generated test files for {test_vector.name} in {output_dir}")
    return {
        'cobol_dir': str(cobol_dir),
        'spark_dir': str(spark_dir),
        'expected_dir': str(expected_dir)
    }


if __name__ == "__main__":
    # Generate files for all test vectors
    from test_vectors import get_all_test_vectors
    
    base_dir = Path(__file__).parent.parent / "golden_datasets"
    
    for tv in get_all_test_vectors():
        output_dir = base_dir / tv.name
        generate_test_files(tv, str(output_dir))
    
    # Also generate comprehensive test
    from test_vectors import get_comprehensive_test_vector
    comprehensive = get_comprehensive_test_vector()
    generate_test_files(comprehensive, str(base_dir / comprehensive.name))
    
    print(f"\nAll test files generated in {base_dir}")
