"""
CBTRN02C - Daily Transaction Posting (PySpark)

Migrated from: app/cbl/CBTRN02C.cbl
COBOL Function: Post records from daily transaction file into the master
                transaction file after validation.

Business Logic (exact replica of COBOL sequential processing):
  1. Read each record from daily_transaction (DALYTRAN) ordered by tran_id
  2. For each transaction, validate using RUNNING account state
     (updated by prior transactions in same batch - like COBOL):
     a. Card number exists in card_xref (XREFFILE)  -> reject code 100
     b. Account exists in account (ACCTFILE)         -> reject code 101
     c. Transaction does not exceed credit limit     -> reject code 102
        Formula: running_cyc_credit - running_cyc_debit + tran_amt <= credit_limit
     d. Account is not expired                       -> reject code 103
        account.expiration_date >= tran orig_ts date portion
  3. If valid:
     a. Update running account state (curr_bal, curr_cyc_credit/debit)
     b. Accumulate tran_cat_bal deltas
     c. Collect for batch write to transaction table
  4. If invalid: collect for batch write to daily_reject
  5. Batch write all results using Delta MERGE for idempotency
  6. Report counts and set return code 4 if any rejects

Idempotency:
  - Transactions already in the transaction table (by tran_id) are skipped
  - Rejects already in daily_reject (by tran_id) are skipped
  - tran_cat_bal updates use Delta MERGE (upsert, not overwrite)
  - account updates use Delta MERGE (additive deltas, not overwrite)
  - Re-running with the same daily_transaction data produces no duplicates

Sequential Processing:
  - Daily transactions are collected and processed one-by-one on the driver
  - Overlimit checks use the running balance updated by prior transactions
  - This exactly replicates COBOL sequential READ + REWRITE behavior
  - Example: Account with credit_limit=5000, curr_cyc_credit=4000
    Txn1 $800 -> running credit=4800, 4800<=5000 -> VALID
    Txn2 $300 -> running credit=5100, 5100>5000  -> REJECTED (overlimit)

Delta tables read:  daily_transaction, card_xref, account, tran_cat_bal
Delta tables write: transaction, account, tran_cat_bal, daily_reject
"""

import sys
from datetime import datetime
from collections import defaultdict

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

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

    print("START OF EXECUTION OF PROGRAM CBTRN02C")

    daily_txn_df = spark.table(f"{db}.daily_transaction")
    xref_df = spark.table(f"{db}.card_xref")
    account_df = spark.table(f"{db}.account")
    existing_txn_df = spark.table(f"{db}.transaction")

    already_posted_ids = set(
        row["tran_id"]
        for row in existing_txn_df.select("tran_id").distinct().collect()
    )

    try:
        existing_reject_df = spark.table(f"{db}.daily_reject")
        already_rejected_ids = set(
            row["tran_id"]
            for row in existing_reject_df.select("tran_id").distinct().collect()
        )
    except Exception:
        already_rejected_ids = set()

    xref_map = {}
    for row in xref_df.select("card_num", "acct_id").collect():
        xref_map[row["card_num"]] = row["acct_id"]

    acct_state = {}
    for row in account_df.collect():
        acct_state[row["acct_id"]] = {
            "curr_bal": float(row["curr_bal"] or 0),
            "credit_limit": float(row["credit_limit"] or 0),
            "expiration_date": row["expiration_date"] or "",
            "curr_cyc_credit": float(row["curr_cyc_credit"] or 0),
            "curr_cyc_debit": float(row["curr_cyc_debit"] or 0),
        }

    daily_rows = daily_txn_df.orderBy("tran_id").collect()
    total_count = len(daily_rows)

    valid_txns = []
    reject_txns = []
    tcatbal_deltas = defaultdict(float)
    acct_deltas = defaultdict(lambda: {"total": 0.0, "credit": 0.0, "debit": 0.0})
    skipped = 0

    for row in daily_rows:
        tran_id = row["tran_id"]

        if tran_id in already_posted_ids or tran_id in already_rejected_ids:
            skipped += 1
            continue

        card_num = row["card_num"]
        tran_amt = float(row["tran_amt"] or 0)
        tran_type_cd = row["tran_type_cd"]
        tran_cat_cd = row["tran_cat_cd"]
        orig_ts = row["orig_ts"] or ""

        base_fields = {
            "tran_id": tran_id,
            "tran_type_cd": tran_type_cd,
            "tran_cat_cd": tran_cat_cd,
            "tran_source": row["tran_source"],
            "tran_desc": row["tran_desc"],
            "tran_amt": tran_amt,
            "merchant_id": row["merchant_id"],
            "merchant_name": row["merchant_name"],
            "merchant_city": row["merchant_city"],
            "merchant_zip": row["merchant_zip"],
            "card_num": card_num,
            "orig_ts": orig_ts,
            "proc_ts": row["proc_ts"],
        }

        if card_num not in xref_map:
            reject_txns.append({
                **base_fields,
                "reject_reason_cd": 100,
                "reject_reason_desc": REJECT_REASONS[100],
            })
            continue

        acct_id = xref_map[card_num]

        if acct_id not in acct_state:
            reject_txns.append({
                **base_fields,
                "reject_reason_cd": 101,
                "reject_reason_desc": REJECT_REASONS[101],
            })
            continue

        acct = acct_state[acct_id]

        if (acct["curr_cyc_credit"] - acct["curr_cyc_debit"] + tran_amt) > acct["credit_limit"]:
            reject_txns.append({
                **base_fields,
                "reject_reason_cd": 102,
                "reject_reason_desc": REJECT_REASONS[102],
            })
            continue

        tran_date = orig_ts[:10] if len(orig_ts) >= 10 else ""
        if acct["expiration_date"] and tran_date and acct["expiration_date"] < tran_date:
            reject_txns.append({
                **base_fields,
                "reject_reason_cd": 103,
                "reject_reason_desc": REJECT_REASONS[103],
            })
            continue

        acct["curr_bal"] += tran_amt
        if tran_amt >= 0:
            acct["curr_cyc_credit"] += tran_amt
        else:
            acct["curr_cyc_debit"] += tran_amt

        tcatbal_deltas[(acct_id, tran_type_cd, tran_cat_cd)] += tran_amt

        ad = acct_deltas[acct_id]
        ad["total"] += tran_amt
        if tran_amt >= 0:
            ad["credit"] += tran_amt
        else:
            ad["debit"] += tran_amt

        valid_txns.append({
            "tran_id": tran_id,
            "tran_type_cd": tran_type_cd,
            "tran_cat_cd": tran_cat_cd,
            "tran_source": row["tran_source"],
            "tran_desc": row["tran_desc"],
            "tran_amt": tran_amt,
            "merchant_id": row["merchant_id"],
            "merchant_name": row["merchant_name"],
            "merchant_city": row["merchant_city"],
            "merchant_zip": row["merchant_zip"],
            "card_num": card_num,
            "orig_ts": orig_ts,
            "proc_ts": now_ts,
        })

    valid_count = len(valid_txns)
    reject_count = len(reject_txns)

    if valid_count > 0:
        txn_schema = T.StructType([
            T.StructField("tran_id", T.StringType()),
            T.StructField("tran_type_cd", T.StringType()),
            T.StructField("tran_cat_cd", T.IntegerType()),
            T.StructField("tran_source", T.StringType()),
            T.StructField("tran_desc", T.StringType()),
            T.StructField("tran_amt", T.DoubleType()),
            T.StructField("merchant_id", T.LongType()),
            T.StructField("merchant_name", T.StringType()),
            T.StructField("merchant_city", T.StringType()),
            T.StructField("merchant_zip", T.StringType()),
            T.StructField("card_num", T.StringType()),
            T.StructField("orig_ts", T.StringType()),
            T.StructField("proc_ts", T.StringType()),
        ])
        valid_df = spark.createDataFrame(valid_txns, schema=txn_schema)
        valid_df.createOrReplaceTempView("_cbtrn02c_new_txns")

        spark.sql(f"""
            MERGE INTO {db}.transaction AS tgt
            USING _cbtrn02c_new_txns AS src
            ON tgt.tran_id = src.tran_id
            WHEN NOT MATCHED THEN INSERT *
        """)

        tcatbal_rows = [
            (acct_id, ttype, tcat, delta)
            for (acct_id, ttype, tcat), delta in tcatbal_deltas.items()
        ]
        tcatbal_delta_df = spark.createDataFrame(
            tcatbal_rows,
            "acct_id BIGINT, tran_type_cd STRING, tran_cat_cd INT, delta_amt DOUBLE",
        )
        tcatbal_delta_df.createOrReplaceTempView("_cbtrn02c_tcatbal_deltas")

        spark.sql(f"""
            MERGE INTO {db}.tran_cat_bal AS tgt
            USING _cbtrn02c_tcatbal_deltas AS src
            ON  tgt.acct_id = src.acct_id
            AND tgt.tran_type_cd = src.tran_type_cd
            AND tgt.tran_cat_cd = src.tran_cat_cd
            WHEN MATCHED THEN UPDATE SET
                tgt.tran_cat_bal = tgt.tran_cat_bal + src.delta_amt
            WHEN NOT MATCHED THEN INSERT
                (acct_id, tran_type_cd, tran_cat_cd, tran_cat_bal)
                VALUES (src.acct_id, src.tran_type_cd, src.tran_cat_cd, src.delta_amt)
        """)

        acct_delta_rows = [
            (acct_id, d["total"], d["credit"], d["debit"])
            for acct_id, d in acct_deltas.items()
        ]
        acct_delta_df = spark.createDataFrame(
            acct_delta_rows,
            "acct_id BIGINT, total_amt DOUBLE, credit_delta DOUBLE, debit_delta DOUBLE",
        )
        acct_delta_df.createOrReplaceTempView("_cbtrn02c_acct_deltas")

        spark.sql(f"""
            MERGE INTO {db}.account AS tgt
            USING _cbtrn02c_acct_deltas AS src
            ON tgt.acct_id = src.acct_id
            WHEN MATCHED THEN UPDATE SET
                tgt.curr_bal = tgt.curr_bal + src.total_amt,
                tgt.curr_cyc_credit = tgt.curr_cyc_credit + src.credit_delta,
                tgt.curr_cyc_debit = tgt.curr_cyc_debit + src.debit_delta
        """)

    if reject_count > 0:
        reject_schema = T.StructType([
            T.StructField("tran_id", T.StringType()),
            T.StructField("tran_type_cd", T.StringType()),
            T.StructField("tran_cat_cd", T.IntegerType()),
            T.StructField("tran_source", T.StringType()),
            T.StructField("tran_desc", T.StringType()),
            T.StructField("tran_amt", T.DoubleType()),
            T.StructField("merchant_id", T.LongType()),
            T.StructField("merchant_name", T.StringType()),
            T.StructField("merchant_city", T.StringType()),
            T.StructField("merchant_zip", T.StringType()),
            T.StructField("card_num", T.StringType()),
            T.StructField("orig_ts", T.StringType()),
            T.StructField("proc_ts", T.StringType()),
            T.StructField("reject_reason_cd", T.IntegerType()),
            T.StructField("reject_reason_desc", T.StringType()),
        ])
        reject_df = spark.createDataFrame(reject_txns, schema=reject_schema)
        reject_df.createOrReplaceTempView("_cbtrn02c_new_rejects")

        spark.sql(f"""
            MERGE INTO {db}.daily_reject AS tgt
            USING _cbtrn02c_new_rejects AS src
            ON tgt.tran_id = src.tran_id
            WHEN NOT MATCHED THEN INSERT *
        """)

    processed = valid_count + reject_count
    return_code = 4 if reject_count > 0 else 0

    print(f"TRANSACTIONS READ      :{total_count:09d}")
    print(f"TRANSACTIONS SKIPPED   :{skipped:09d} (already processed)")
    print(f"TRANSACTIONS POSTED    :{valid_count:09d}")
    print(f"TRANSACTIONS REJECTED  :{reject_count:09d}")
    print("END OF EXECUTION OF PROGRAM CBTRN02C")

    return {
        "return_code": return_code,
        "total_read": total_count,
        "skipped": skipped,
        "processed": processed,
        "valid": valid_count,
        "rejected": reject_count,
    }


if __name__ == "__main__":
    catalog = sys.argv[1] if len(sys.argv) > 1 else ""
    database = sys.argv[2] if len(sys.argv) > 2 else "carddemo"
    result = run(catalog, database)
    sys.exit(result["return_code"])
