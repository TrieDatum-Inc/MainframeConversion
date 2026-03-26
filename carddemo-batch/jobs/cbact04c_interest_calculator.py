"""
CBACT04C - Interest Calculator (PySpark)

Migrated from: app/cbl/CBACT04C.cbl
COBOL Function: Compute monthly interest charges for each account based on
                transaction category balances and disclosure group rates.

Business Logic (exact replica of COBOL):
  1. Read tran_cat_bal sequentially (ordered by acct_id)
  2. For each account (when acct_id changes):
     a. Read the account record from account table
     b. Use account.group_id to look up interest rates
  3. For each tran_cat_bal row:
     a. Look up the interest rate from disclosure_group using
        (account.group_id, tran_type_cd, tran_cat_cd)
     b. If not found, try with group_id = 'DEFAULT'
     c. If int_rate != 0:
        - Compute monthly interest = (tran_cat_bal * int_rate) / 1200
        - Accumulate total interest per account
        - Write an interest transaction to the transaction table:
          tran_type_cd='01', tran_cat_cd=5 (Interest), source='System',
          desc='Int. for a/c {acct_id}'
  4. After processing all rows for an account:
     a. Update account: curr_bal += total_interest
     b. Reset curr_cyc_credit = 0, curr_cyc_debit = 0
  5. 1400-COMPUTE-FEES is a stub in COBOL ("To be implemented")

Idempotency:
  - Interest transaction IDs are deterministic: {parm_date}{sequence}
  - Before writing, existing interest txns for the same parm_date are checked
  - If already run for parm_date, the job skips with a message
  - Account updates use Delta MERGE (not overwrite) so re-runs are safe

Fix from v1: card_xref join used one card per account (first card_num) to
  prevent duplicate interest when an account has multiple cards.

Input parameter: parm_date (YYYY-MM-DD) used to construct interest tran_id

Delta tables read:  tran_cat_bal, account, card_xref, disclosure_group
Delta tables write: transaction, account
"""

import sys
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.window import Window
import pyspark.sql.functions as F
from pyspark.sql import types as T

sys.path.insert(0, "..")
from utils.spark_utils import get_spark_session, get_db_prefix

INTEREST_TRAN_ID_PREFIX_FORMAT = "%Y%m%d"


def run(
    parm_date: str = "",
    catalog: str = "",
    database: str = "carddemo",
) -> dict:
    spark = get_spark_session("CBACT04C_InterestCalculator")
    db = get_db_prefix(catalog, database)

    if not parm_date:
        parm_date = datetime.now().strftime("%Y-%m-%d")

    run_prefix = parm_date.replace("-", "")
    now_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")

    print("START OF EXECUTION OF PROGRAM CBACT04C")

    existing_txn_df = spark.table(f"{db}.transactions")
    already_run = existing_txn_df.filter(
        F.col("tran_id").startswith(run_prefix)
        & (F.col("tran_source") == "System")
        & F.col("tran_desc").startswith("Int. for a/c")
    ).count()

    if already_run > 0:
        print(f"ALREADY PROCESSED FOR {parm_date}: {already_run} interest txns exist. SKIPPING.")
        print("END OF EXECUTION OF PROGRAM CBACT04C")
        return {"return_code": 0, "records_processed": 0, "skipped": True}

    tcatbal_df = spark.table(f"{db}.tran_cat_bal")
    account_df = spark.table(f"{db}.account")
    xref_df = spark.table(f"{db}.card_xref")
    discgrp_df = spark.table(f"{db}.disclosure_group")

    first_card_per_acct = xref_df.groupBy("acct_id").agg(
        F.first("card_num").alias("card_num")
    )

    tcatbal_with_acct = tcatbal_df.alias("tc").join(
        account_df.alias("ac"),
        F.col("tc.acct_id") == F.col("ac.acct_id"),
        "inner",
    ).join(
        first_card_per_acct.alias("xr"),
        F.col("tc.acct_id") == F.col("xr.acct_id"),
        "inner",
    ).select(
        F.col("tc.acct_id"),
        F.col("tc.tran_type_cd"),
        F.col("tc.tran_cat_cd"),
        F.col("tc.tran_cat_bal"),
        F.col("ac.group_id"),
        F.col("xr.card_num"),
    )

    with_rate = tcatbal_with_acct.alias("t").join(
        discgrp_df.alias("dg"),
        (F.col("t.group_id") == F.col("dg.acct_group_id"))
        & (F.col("t.tran_type_cd") == F.col("dg.tran_type_cd"))
        & (F.col("t.tran_cat_cd") == F.col("dg.tran_cat_cd")),
        "left",
    ).select(
        F.col("t.acct_id"),
        F.col("t.tran_type_cd"),
        F.col("t.tran_cat_cd"),
        F.col("t.tran_cat_bal"),
        F.col("t.group_id"),
        F.col("t.card_num"),
        F.col("dg.int_rate").alias("group_rate"),
    )

    default_rates = discgrp_df.filter(F.col("acct_group_id") == "DEFAULT").alias("dr")

    with_final_rate = with_rate.alias("w").join(
        default_rates,
        (F.col("w.tran_type_cd") == F.col("dr.tran_type_cd"))
        & (F.col("w.tran_cat_cd") == F.col("dr.tran_cat_cd")),
        "left",
    ).select(
        F.col("w.acct_id"),
        F.col("w.tran_type_cd"),
        F.col("w.tran_cat_cd"),
        F.col("w.tran_cat_bal"),
        F.col("w.card_num"),
        F.coalesce(F.col("w.group_rate"), F.col("dr.int_rate"), F.lit(0)).alias("int_rate"),
    )

    with_interest = with_final_rate.filter(F.col("int_rate") != 0).withColumn(
        "monthly_interest",
        F.round((F.col("tran_cat_bal") * F.col("int_rate")) / F.lit(1200), 2),
    )

    record_count = with_interest.count()

    if record_count > 0:
        interest_with_id = with_interest.withColumn(
            "row_num",
            F.row_number().over(
                Window.orderBy("acct_id", "tran_type_cd", "tran_cat_cd")
            ),
        ).withColumn(
            "tran_id",
            F.concat(
                F.lit(run_prefix),
                F.lpad(F.col("row_num").cast("string"), 6, "0"),
            ),
        )

        interest_txns = interest_with_id.select(
            F.col("tran_id"),
            F.lit("01").alias("tran_type_cd"),
            F.lit(5).alias("tran_cat_cd"),
            F.lit("System").alias("tran_source"),
            F.concat(F.lit("Int. for a/c "), F.col("acct_id").cast("string")).alias("tran_desc"),
            F.col("monthly_interest").alias("tran_amt"),
            F.lit(0).cast("long").alias("merchant_id"),
            F.lit("").alias("merchant_name"),
            F.lit("").alias("merchant_city"),
            F.lit("").alias("merchant_zip"),
            F.col("card_num"),
            F.lit(now_ts).alias("orig_ts"),
            F.lit(now_ts).alias("proc_ts"),
        )

        interest_txns.createOrReplaceTempView("_cbact04c_interest_txns")

        spark.sql(f"""
            MERGE INTO {db}.transactions AS tgt
            USING _cbact04c_interest_txns AS src
            ON tgt.tran_id = src.tran_id
            WHEN NOT MATCHED THEN INSERT *
        """)

        total_interest_per_acct = with_interest.groupBy("acct_id").agg(
            F.sum("monthly_interest").alias("total_interest")
        )

        total_interest_per_acct.createOrReplaceTempView("_cbact04c_acct_interest")

        spark.sql(f"""
            MERGE INTO {db}.account AS tgt
            USING _cbact04c_acct_interest AS src
            ON tgt.acct_id = src.acct_id
            WHEN MATCHED THEN UPDATE SET
                tgt.curr_bal = tgt.curr_bal + src.total_interest,
                tgt.curr_cyc_credit = 0,
                tgt.curr_cyc_debit = 0
        """)

    print(f"RECORDS PROCESSED: {record_count}")
    print("END OF EXECUTION OF PROGRAM CBACT04C")

    return {"return_code": 0, "records_processed": record_count, "skipped": False}


if __name__ == "__main__":
    parm_date = sys.argv[1] if len(sys.argv) > 1 else ""
    catalog = sys.argv[2] if len(sys.argv) > 2 else ""
    database = sys.argv[3] if len(sys.argv) > 3 else "carddemo"
    result = run(parm_date, catalog, database)
    sys.exit(result["return_code"])
