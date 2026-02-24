"""
CBTRN02C - Daily Transaction Posting (PySpark)

Migrated from: app/cbl/CBTRN02C.cbl
COBOL Function: Post records from daily transaction file into the master
                transaction file after validation.

Business Logic (exact replica of COBOL):
  1. Read each record from daily_transaction (DALYTRAN)
  2. Validate:
     a. Card number exists in card_xref (XREFFILE)  -> reject code 100
     b. Account exists in account (ACCTFILE)         -> reject code 101
     c. Transaction does not exceed credit limit     -> reject code 102
        Formula: curr_cyc_credit - curr_cyc_debit + tran_amt <= credit_limit
     d. Account is not expired                       -> reject code 103
        account.expiration_date >= tran orig_ts date portion
  3. If valid:
     a. Update tran_cat_bal (create if not exists, else add tran_amt)
     b. Update account balances:
        - curr_bal += tran_amt
        - if tran_amt >= 0: curr_cyc_credit += tran_amt
        - else:             curr_cyc_debit  += tran_amt
     c. Write record to transaction table with proc_ts = current timestamp
  4. If invalid: write to daily_reject with reason code + description
  5. Report counts and set return code 4 if any rejects

Delta tables read:  daily_transaction, card_xref, account, tran_cat_bal
Delta tables write: transaction, account, tran_cat_bal, daily_reject
"""

import sys
from datetime import datetime
from decimal import Decimal

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

sys.path.insert(0, "..")
from utils.spark_utils import get_spark_session, get_db_prefix

REJECT_REASONS = {
    100: "INVALID CARD NUMBER FOUND",
    101: "ACCOUNT RECORD NOT FOUND",
    102: "OVERLIMIT TRANSACTION",
    103: "TRANSACTION RECEIVED AFTER ACCT EXPIRATION",
}


def run(catalog: str = "", database: str = "carddemo") -> dict:
    spark = get_spark_session("CBTRN02C_DailyTransactionPosting")
    db = get_db_prefix(catalog, database)
    now_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")

    daily_txn_df = spark.table(f"{db}.daily_transaction")
    xref_df = spark.table(f"{db}.card_xref")
    account_df = spark.table(f"{db}.account")
    tcatbal_df = spark.table(f"{db}.tran_cat_bal")

    total_count = daily_txn_df.count()

    joined = daily_txn_df.alias("dt").join(
        xref_df.alias("xr"),
        F.col("dt.card_num") == F.col("xr.card_num"),
        "left",
    )

    no_xref = joined.filter(F.col("xr.card_num").isNull())
    has_xref = joined.filter(F.col("xr.card_num").isNotNull())

    reject_100 = no_xref.select(
        F.col("dt.tran_id"),
        F.col("dt.tran_type_cd"),
        F.col("dt.tran_cat_cd"),
        F.col("dt.tran_source"),
        F.col("dt.tran_desc"),
        F.col("dt.tran_amt"),
        F.col("dt.merchant_id"),
        F.col("dt.merchant_name"),
        F.col("dt.merchant_city"),
        F.col("dt.merchant_zip"),
        F.col("dt.card_num"),
        F.col("dt.orig_ts"),
        F.col("dt.proc_ts"),
        F.lit(100).alias("reject_reason_cd"),
        F.lit(REJECT_REASONS[100]).alias("reject_reason_desc"),
    )

    with_acct = has_xref.join(
        account_df.alias("ac"),
        F.col("xr.acct_id") == F.col("ac.acct_id"),
        "left",
    )

    no_acct = with_acct.filter(F.col("ac.acct_id").isNull())
    has_acct = with_acct.filter(F.col("ac.acct_id").isNotNull())

    reject_101 = no_acct.select(
        F.col("dt.tran_id"),
        F.col("dt.tran_type_cd"),
        F.col("dt.tran_cat_cd"),
        F.col("dt.tran_source"),
        F.col("dt.tran_desc"),
        F.col("dt.tran_amt"),
        F.col("dt.merchant_id"),
        F.col("dt.merchant_name"),
        F.col("dt.merchant_city"),
        F.col("dt.merchant_zip"),
        F.col("dt.card_num"),
        F.col("dt.orig_ts"),
        F.col("dt.proc_ts"),
        F.lit(101).alias("reject_reason_cd"),
        F.lit(REJECT_REASONS[101]).alias("reject_reason_desc"),
    )

    overlimit = has_acct.filter(
        (F.col("ac.curr_cyc_credit") - F.col("ac.curr_cyc_debit") + F.col("dt.tran_amt"))
        > F.col("ac.credit_limit")
    )
    within_limit = has_acct.filter(
        (F.col("ac.curr_cyc_credit") - F.col("ac.curr_cyc_debit") + F.col("dt.tran_amt"))
        <= F.col("ac.credit_limit")
    )

    reject_102 = overlimit.select(
        F.col("dt.tran_id"),
        F.col("dt.tran_type_cd"),
        F.col("dt.tran_cat_cd"),
        F.col("dt.tran_source"),
        F.col("dt.tran_desc"),
        F.col("dt.tran_amt"),
        F.col("dt.merchant_id"),
        F.col("dt.merchant_name"),
        F.col("dt.merchant_city"),
        F.col("dt.merchant_zip"),
        F.col("dt.card_num"),
        F.col("dt.orig_ts"),
        F.col("dt.proc_ts"),
        F.lit(102).alias("reject_reason_cd"),
        F.lit(REJECT_REASONS[102]).alias("reject_reason_desc"),
    )

    expired = within_limit.filter(
        F.col("ac.expiration_date") < F.substring(F.col("dt.orig_ts"), 1, 10)
    )
    not_expired = within_limit.filter(
        F.col("ac.expiration_date") >= F.substring(F.col("dt.orig_ts"), 1, 10)
    )

    reject_103 = expired.select(
        F.col("dt.tran_id"),
        F.col("dt.tran_type_cd"),
        F.col("dt.tran_cat_cd"),
        F.col("dt.tran_source"),
        F.col("dt.tran_desc"),
        F.col("dt.tran_amt"),
        F.col("dt.merchant_id"),
        F.col("dt.merchant_name"),
        F.col("dt.merchant_city"),
        F.col("dt.merchant_zip"),
        F.col("dt.card_num"),
        F.col("dt.orig_ts"),
        F.col("dt.proc_ts"),
        F.lit(103).alias("reject_reason_cd"),
        F.lit(REJECT_REASONS[103]).alias("reject_reason_desc"),
    )

    all_rejects = reject_100.unionByName(reject_101).unionByName(reject_102).unionByName(reject_103)
    reject_count = all_rejects.count()

    if reject_count > 0:
        all_rejects.write.format("delta").mode("append").saveAsTable(f"{db}.daily_reject")

    valid_txns = not_expired.select(
        F.col("dt.tran_id"),
        F.col("dt.tran_type_cd"),
        F.col("dt.tran_cat_cd"),
        F.col("dt.tran_source"),
        F.col("dt.tran_desc"),
        F.col("dt.tran_amt"),
        F.col("dt.merchant_id"),
        F.col("dt.merchant_name"),
        F.col("dt.merchant_city"),
        F.col("dt.merchant_zip"),
        F.col("dt.card_num"),
        F.col("dt.orig_ts"),
        F.lit(now_ts).alias("proc_ts"),
        F.col("xr.acct_id"),
    )

    valid_count = valid_txns.count()

    if valid_count > 0:
        txn_insert = valid_txns.select(
            "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
            "tran_amt", "merchant_id", "merchant_name", "merchant_city", "merchant_zip",
            "card_num", "orig_ts", "proc_ts",
        )
        txn_insert.write.format("delta").mode("append").saveAsTable(f"{db}.transaction")

        tcatbal_delta = valid_txns.groupBy("acct_id", "tran_type_cd", "tran_cat_cd").agg(
            F.sum("tran_amt").alias("delta_amt")
        )

        existing_tcatbal = tcatbal_df.alias("tc").join(
            tcatbal_delta.alias("d"),
            (F.col("tc.acct_id") == F.col("d.acct_id"))
            & (F.col("tc.tran_type_cd") == F.col("d.tran_type_cd"))
            & (F.col("tc.tran_cat_cd") == F.col("d.tran_cat_cd")),
            "inner",
        ).select(
            F.col("tc.acct_id"),
            F.col("tc.tran_type_cd"),
            F.col("tc.tran_cat_cd"),
            (F.col("tc.tran_cat_bal") + F.col("d.delta_amt")).alias("tran_cat_bal"),
        )

        new_tcatbal = tcatbal_delta.alias("d").join(
            tcatbal_df.alias("tc"),
            (F.col("d.acct_id") == F.col("tc.acct_id"))
            & (F.col("d.tran_type_cd") == F.col("tc.tran_type_cd"))
            & (F.col("d.tran_cat_cd") == F.col("tc.tran_cat_cd")),
            "left_anti",
        ).select(
            F.col("d.acct_id"),
            F.col("d.tran_type_cd"),
            F.col("d.tran_cat_cd"),
            F.col("d.delta_amt").alias("tran_cat_bal"),
        )

        merged_tcatbal = existing_tcatbal.unionByName(new_tcatbal)

        unchanged_tcatbal = tcatbal_df.alias("tc").join(
            tcatbal_delta.alias("d"),
            (F.col("tc.acct_id") == F.col("d.acct_id"))
            & (F.col("tc.tran_type_cd") == F.col("d.tran_type_cd"))
            & (F.col("tc.tran_cat_cd") == F.col("d.tran_cat_cd")),
            "left_anti",
        )

        final_tcatbal = unchanged_tcatbal.unionByName(merged_tcatbal)
        final_tcatbal.write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(f"{db}.tran_cat_bal")

        acct_delta = valid_txns.groupBy("acct_id").agg(
            F.sum("tran_amt").alias("total_amt"),
            F.sum(F.when(F.col("tran_amt") >= 0, F.col("tran_amt")).otherwise(F.lit(0))).alias("credit_delta"),
            F.sum(F.when(F.col("tran_amt") < 0, F.col("tran_amt")).otherwise(F.lit(0))).alias("debit_delta"),
        )

        updated_accounts = account_df.alias("ac").join(
            acct_delta.alias("ad"),
            F.col("ac.acct_id") == F.col("ad.acct_id"),
            "left",
        ).select(
            F.col("ac.acct_id"),
            F.col("ac.active_status"),
            (F.col("ac.curr_bal") + F.coalesce(F.col("ad.total_amt"), F.lit(0))).alias("curr_bal"),
            F.col("ac.credit_limit"),
            F.col("ac.cash_credit_limit"),
            F.col("ac.open_date"),
            F.col("ac.expiration_date"),
            F.col("ac.reissue_date"),
            (F.col("ac.curr_cyc_credit") + F.coalesce(F.col("ad.credit_delta"), F.lit(0))).alias("curr_cyc_credit"),
            (F.col("ac.curr_cyc_debit") + F.coalesce(F.col("ad.debit_delta"), F.lit(0))).alias("curr_cyc_debit"),
            F.col("ac.addr_zip"),
            F.col("ac.group_id"),
        )

        updated_accounts.write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(f"{db}.account")

    processed = valid_count + reject_count
    return_code = 4 if reject_count > 0 else 0

    print(f"START OF EXECUTION OF PROGRAM CBTRN02C")
    print(f"TRANSACTIONS PROCESSED :{processed:09d}")
    print(f"TRANSACTIONS REJECTED  :{reject_count:09d}")
    print(f"END OF EXECUTION OF PROGRAM CBTRN02C")

    return {
        "return_code": return_code,
        "total_read": total_count,
        "processed": processed,
        "valid": valid_count,
        "rejected": reject_count,
    }


if __name__ == "__main__":
    catalog = sys.argv[1] if len(sys.argv) > 1 else ""
    database = sys.argv[2] if len(sys.argv) > 2 else "carddemo"
    result = run(catalog, database)
    sys.exit(result["return_code"])
