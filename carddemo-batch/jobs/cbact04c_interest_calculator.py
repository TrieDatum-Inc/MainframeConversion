"""
CBACT04C - Interest Calculator (PySpark)

Migrated from: app/cbl/CBACT04C.cbl
COBOL Function: Compute monthly interest charges for each account based on
                transaction category balances and disclosure group rates.

Business Logic (exact replica of COBOL):
  1. Read tran_cat_bal sequentially (ordered by acct_id)
  2. For each account (when acct_id changes):
     a. Read the account record from account table
     b. Read the card_xref record to get group_id linkage
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

Input parameter: parm_date (YYYY-MM-DD) used to construct interest tran_id

Delta tables read:  tran_cat_bal, account, card_xref, disclosure_group
Delta tables write: transaction, account
"""

import sys
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

sys.path.insert(0, "..")
from utils.spark_utils import get_spark_session, get_db_prefix


def run(
    parm_date: str = "",
    catalog: str = "",
    database: str = "carddemo",
) -> dict:
    spark = get_spark_session("CBACT04C_InterestCalculator")
    db = get_db_prefix(catalog, database)

    if not parm_date:
        parm_date = datetime.now().strftime("%Y-%m-%d")

    now_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")

    print("START OF EXECUTION OF PROGRAM CBACT04C")

    tcatbal_df = spark.table(f"{db}.tran_cat_bal")
    account_df = spark.table(f"{db}.account")
    xref_df = spark.table(f"{db}.card_xref")
    discgrp_df = spark.table(f"{db}.disclosure_group")

    tcatbal_with_acct = tcatbal_df.alias("tc").join(
        account_df.alias("ac"),
        F.col("tc.acct_id") == F.col("ac.acct_id"),
        "inner",
    ).join(
        xref_df.alias("xr"),
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
                F.Window.orderBy("acct_id", "tran_type_cd", "tran_cat_cd")
            ),
        ).withColumn(
            "tran_id",
            F.concat(
                F.lit(parm_date.replace("-", "")),
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

        interest_txns.write.format("delta").mode("append").saveAsTable(
            f"{db}.transaction"
        )

        total_interest_per_acct = with_interest.groupBy("acct_id").agg(
            F.sum("monthly_interest").alias("total_interest")
        )

        updated_accounts = account_df.alias("ac").join(
            total_interest_per_acct.alias("ti"),
            F.col("ac.acct_id") == F.col("ti.acct_id"),
            "left",
        ).select(
            F.col("ac.acct_id"),
            F.col("ac.active_status"),
            F.when(
                F.col("ti.total_interest").isNotNull(),
                F.col("ac.curr_bal") + F.col("ti.total_interest"),
            ).otherwise(F.col("ac.curr_bal")).alias("curr_bal"),
            F.col("ac.credit_limit"),
            F.col("ac.cash_credit_limit"),
            F.col("ac.open_date"),
            F.col("ac.expiration_date"),
            F.col("ac.reissue_date"),
            F.when(
                F.col("ti.total_interest").isNotNull(), F.lit(0).cast("decimal(12,2)")
            ).otherwise(F.col("ac.curr_cyc_credit")).alias("curr_cyc_credit"),
            F.when(
                F.col("ti.total_interest").isNotNull(), F.lit(0).cast("decimal(12,2)")
            ).otherwise(F.col("ac.curr_cyc_debit")).alias("curr_cyc_debit"),
            F.col("ac.addr_zip"),
            F.col("ac.group_id"),
        )

        updated_accounts.write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(f"{db}.account")

    print(f"RECORDS PROCESSED: {record_count}")
    print("END OF EXECUTION OF PROGRAM CBACT04C")

    return {"return_code": 0, "records_processed": record_count}


if __name__ == "__main__":
    parm_date = sys.argv[1] if len(sys.argv) > 1 else ""
    catalog = sys.argv[2] if len(sys.argv) > 2 else ""
    database = sys.argv[3] if len(sys.argv) > 3 else "carddemo"
    result = run(parm_date, catalog, database)
    sys.exit(result["return_code"])
