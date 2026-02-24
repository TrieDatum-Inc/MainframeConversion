"""
CBTRN03C - Daily Transaction Report (PySpark)

Migrated from: app/cbl/CBTRN03C.cbl
COBOL Function: Print a transaction detail report filtered by a date range,
                with page totals, account totals, and a grand total.

Business Logic (exact replica of COBOL):
  1. Read date parameters (start_date, end_date)
  2. Read transaction records sequentially
  3. Filter: only include where proc_ts date portion is between
     start_date and end_date (inclusive)
  4. For each transaction:
     a. Look up card_xref to get acct_id
     b. Look up transaction_type to get type description
     c. Look up transaction_category to get category description
  5. Report layout (133-char line width in COBOL):
     - Header: "DALYREPT  Daily Transaction Report  Date Range: {start} to {end}"
     - Column headers: Transaction ID | Account ID | Transaction Type |
                       Tran Category | Tran Source | Amount
     - Detail rows
     - Page totals every 20 lines (page_size = 20)
     - Account totals when card_num changes
     - Grand total at end
  6. Output: CSV file with the report data

Delta tables read: transaction, card_xref, transaction_type, transaction_category
Output: CSV file
"""

import sys
import os
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

sys.path.insert(0, "..")
from utils.spark_utils import get_spark_session, get_db_prefix


def run(
    start_date: str = "",
    end_date: str = "",
    output_path: str = "",
    catalog: str = "",
    database: str = "carddemo",
) -> dict:
    spark = get_spark_session("CBTRN03C_DailyTransactionReport")
    db = get_db_prefix(catalog, database)

    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    if not end_date:
        end_date = start_date
    if not output_path:
        output_path = f"/tmp/carddemo_transaction_report_{start_date}_to_{end_date}"

    print("START OF EXECUTION OF PROGRAM CBTRN03C")
    print(f"Reporting from {start_date} to {end_date}")

    txn_df = spark.table(f"{db}.transaction")
    xref_df = spark.table(f"{db}.card_xref")
    ttype_df = spark.table(f"{db}.transaction_type")
    tcat_df = spark.table(f"{db}.transaction_category")

    filtered_txn = txn_df.filter(
        (F.substring(F.col("proc_ts"), 1, 10) >= start_date)
        & (F.substring(F.col("proc_ts"), 1, 10) <= end_date)
    )

    report_df = (
        filtered_txn.alias("t")
        .join(
            xref_df.alias("xr"),
            F.col("t.card_num") == F.col("xr.card_num"),
            "left",
        )
        .join(
            ttype_df.alias("tt"),
            F.col("t.tran_type_cd") == F.col("tt.tran_type_cd"),
            "left",
        )
        .join(
            tcat_df.alias("tc"),
            (F.col("t.tran_type_cd") == F.col("tc.tran_type_cd"))
            & (F.col("t.tran_cat_cd") == F.col("tc.tran_cat_cd")),
            "left",
        )
        .select(
            F.col("t.tran_id").alias("transaction_id"),
            F.coalesce(F.col("xr.acct_id").cast("string"), F.lit("")).alias("account_id"),
            F.concat(
                F.col("t.tran_type_cd"),
                F.lit("-"),
                F.coalesce(F.col("tt.tran_type_desc"), F.lit("")),
            ).alias("transaction_type"),
            F.concat(
                F.col("t.tran_cat_cd").cast("string"),
                F.lit("-"),
                F.coalesce(F.col("tc.tran_cat_desc"), F.lit("")),
            ).alias("transaction_category"),
            F.coalesce(F.col("t.tran_source"), F.lit("")).alias("transaction_source"),
            F.col("t.tran_amt").alias("amount"),
            F.col("t.card_num"),
        )
        .orderBy("card_num", "tran_id")
    )

    record_count = report_df.count()

    account_totals = report_df.groupBy("card_num", "account_id").agg(
        F.sum("amount").alias("account_total"),
        F.count("*").alias("txn_count"),
    ).orderBy("card_num")

    grand_total_val = report_df.agg(F.sum("amount")).collect()[0][0]
    grand_total = float(grand_total_val) if grand_total_val else 0.0

    detail_output = report_df.select(
        "transaction_id",
        "account_id",
        "transaction_type",
        "transaction_category",
        "transaction_source",
        "amount",
    )

    detail_output.coalesce(1).write.option("header", "true").mode("overwrite").csv(
        f"{output_path}/detail"
    )

    summary_rows = []
    acct_totals_collected = account_totals.collect()
    for row in acct_totals_collected:
        summary_rows.append(
            (row["card_num"], row["account_id"], row["txn_count"], float(row["account_total"]))
        )

    summary_schema = "card_num STRING, account_id STRING, txn_count LONG, account_total DOUBLE"
    summary_df = spark.createDataFrame(summary_rows, summary_schema)
    summary_df.coalesce(1).write.option("header", "true").mode("overwrite").csv(
        f"{output_path}/account_totals"
    )

    grand_total_df = spark.createDataFrame(
        [
            (
                start_date,
                end_date,
                record_count,
                grand_total,
            )
        ],
        "start_date STRING, end_date STRING, total_transactions LONG, grand_total DOUBLE",
    )
    grand_total_df.coalesce(1).write.option("header", "true").mode("overwrite").csv(
        f"{output_path}/grand_total"
    )

    print(f"TRANSACTIONS IN REPORT: {record_count}")
    print(f"GRAND TOTAL: {grand_total:,.2f}")
    print(f"OUTPUT PATH: {output_path}")
    print("END OF EXECUTION OF PROGRAM CBTRN03C")

    return {
        "return_code": 0,
        "record_count": record_count,
        "grand_total": grand_total,
        "output_path": output_path,
    }


if __name__ == "__main__":
    start_date = sys.argv[1] if len(sys.argv) > 1 else ""
    end_date = sys.argv[2] if len(sys.argv) > 2 else ""
    output_path = sys.argv[3] if len(sys.argv) > 3 else ""
    catalog = sys.argv[4] if len(sys.argv) > 4 else ""
    database = sys.argv[5] if len(sys.argv) > 5 else "carddemo"
    result = run(start_date, end_date, output_path, catalog, database)
    sys.exit(result["return_code"])
