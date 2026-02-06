"""
PySpark Migration of CBTRN02C - Post Daily Transactions

Original: app/cbl/CBTRN02C.cbl (COBOL Batch Program)
JCL:      app/jcl/POSTTRAN.jcl

Business Logic:
    Reads daily transaction records, validates each against the card cross-reference
    and account master files, posts valid transactions to the transaction master,
    updates account balances and transaction category balances, and writes rejected
    transactions with failure reasons.

Validation Rules (from CBTRN02C PROCEDURE DIVISION):
    100 - Card number not found in cross-reference file
    101 - Account record not found for the cross-referenced account ID
    102 - Transaction would exceed account credit limit (overlimit)
    103 - Transaction received after account expiration date

Copybooks Used:
    CVTRA06Y - Daily transaction record layout
    CVTRA05Y - Transaction record layout
    CVACT03Y - Card cross-reference record layout
    CVACT01Y - Account record layout
    CVTRA01Y - Transaction category balance record layout

Input Delta Tables:
    carddemo.daily_transaction  (DALYTRAN)
    carddemo.card_xref          (XREFFILE)
    carddemo.account            (ACCTFILE)

Output Delta Tables:
    carddemo.transaction        (TRANFILE)
    carddemo.daily_rejects      (DALYREJS)

Updated Delta Tables:
    carddemo.account            (ACCTFILE - balances updated)
    carddemo.tran_cat_balance   (TCATBALF - category balances updated/inserted)
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable


SCHEMA = "carddemo"

REJECT_INVALID_CARD = 100
REJECT_ACCOUNT_NOT_FOUND = 101
REJECT_OVERLIMIT = 102
REJECT_EXPIRED = 103


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("CBTRN02C_PostDailyTransactions")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .getOrCreate()
    )


def load_input_tables(spark: SparkSession) -> tuple:
    daily_tran = spark.table(f"{SCHEMA}.daily_transaction")
    card_xref = spark.table(f"{SCHEMA}.card_xref")
    account = spark.table(f"{SCHEMA}.account")
    return daily_tran, card_xref, account


def validate_and_split(
    daily_tran: DataFrame,
    card_xref: DataFrame,
    account: DataFrame,
) -> tuple:
    """
    Replicates CBTRN02C validation logic (paragraphs 1500-VALIDATE-TRAN,
    1500-A-LOOKUP-XREF, 1500-B-LOOKUP-ACCT).

    Validation sequence per the original COBOL:
      1. Look up card number in XREF -> reject 100 if missing
      2. Look up account by XREF account ID -> reject 101 if missing
      3. Compute temp_bal = cyc_credit - cyc_debit + tran_amt
         -> reject 102 if credit_limit < temp_bal
      4. Check expiration_date >= tran_orig_ts(1:10)
         -> reject 103 if expired

    The COBOL program processes records sequentially, so earlier transactions
    update the account before later ones are validated. To preserve this
    behaviour in a set-based engine we use a window-based running sum of
    transaction amounts per account, ordered by the original timestamp and
    transaction ID.
    """
    xref_lookup = daily_tran.join(
        card_xref,
        daily_tran["dalytran_card_num"] == card_xref["xref_card_num"],
        "left",
    )

    no_xref = xref_lookup.filter(F.col("xref_card_num").isNull())
    rejects_100 = (
        no_xref
        .select(daily_tran["*"])
        .withColumn("reject_reason_code", F.lit(REJECT_INVALID_CARD))
        .withColumn("reject_reason_desc", F.lit("INVALID CARD NUMBER FOUND"))
    )

    has_xref = xref_lookup.filter(F.col("xref_card_num").isNotNull())

    acct_lookup = has_xref.join(
        account,
        has_xref["xref_acct_id"] == account["acct_id"],
        "left",
    )

    no_acct = acct_lookup.filter(F.col("acct_id").isNull())
    rejects_101 = (
        no_acct
        .select(daily_tran["*"])
        .withColumn("reject_reason_code", F.lit(REJECT_ACCOUNT_NOT_FOUND))
        .withColumn("reject_reason_desc", F.lit("ACCOUNT RECORD NOT FOUND"))
    )

    has_acct = acct_lookup.filter(F.col("acct_id").isNotNull())

    running_window = (
        Window
        .partitionBy("acct_id")
        .orderBy("dalytran_orig_ts", "dalytran_id")
        .rowsBetween(Window.unboundedPreceding, Window.currentRow)
    )

    with_running = has_acct.withColumn(
        "running_amt_sum",
        F.sum("dalytran_amt").over(running_window),
    ).withColumn(
        "temp_bal",
        F.col("acct_curr_cyc_credit")
        - F.col("acct_curr_cyc_debit")
        + F.col("running_amt_sum"),
    )

    rejects_102 = (
        with_running
        .filter(F.col("acct_credit_limit") < F.col("temp_bal"))
        .select(daily_tran["*"])
        .withColumn("reject_reason_code", F.lit(REJECT_OVERLIMIT))
        .withColumn("reject_reason_desc", F.lit("OVERLIMIT TRANSACTION"))
    )

    within_limit = with_running.filter(
        F.col("acct_credit_limit") >= F.col("temp_bal")
    )

    rejects_103 = (
        within_limit
        .filter(
            F.col("acct_expiration_date")
            < F.substring("dalytran_orig_ts", 1, 10)
        )
        .select(daily_tran["*"])
        .withColumn("reject_reason_code", F.lit(REJECT_EXPIRED))
        .withColumn(
            "reject_reason_desc",
            F.lit("TRANSACTION RECEIVED AFTER ACCT EXPIRATION"),
        )
    )

    valid = within_limit.filter(
        F.col("acct_expiration_date")
        >= F.substring("dalytran_orig_ts", 1, 10)
    )

    all_rejects = (
        rejects_100
        .unionByName(rejects_101)
        .unionByName(rejects_102)
        .unionByName(rejects_103)
    )

    return valid, all_rejects


def post_transactions(spark: SparkSession, valid: DataFrame) -> None:
    """
    Replicates CBTRN02C paragraph 2000-POST-TRANSACTION and
    2900-WRITE-TRANSACTION-FILE.

    Maps daily transaction fields to the transaction master record layout
    and inserts into the transaction Delta table.
    """
    proc_ts = F.date_format(F.current_timestamp(), "yyyy-MM-dd-HH.mm.ss.SSSSSS")

    posted = valid.select(
        F.col("dalytran_id").alias("tran_id"),
        F.col("dalytran_type_cd").alias("tran_type_cd"),
        F.col("dalytran_cat_cd").alias("tran_cat_cd"),
        F.col("dalytran_source").alias("tran_source"),
        F.col("dalytran_desc").alias("tran_desc"),
        F.col("dalytran_amt").alias("tran_amt"),
        F.col("dalytran_merchant_id").alias("tran_merchant_id"),
        F.col("dalytran_merchant_name").alias("tran_merchant_name"),
        F.col("dalytran_merchant_city").alias("tran_merchant_city"),
        F.col("dalytran_merchant_zip").alias("tran_merchant_zip"),
        F.col("dalytran_card_num").alias("tran_card_num"),
        F.col("dalytran_orig_ts").alias("tran_orig_ts"),
        proc_ts.alias("tran_proc_ts"),
    )

    posted.write.format("delta").mode("append").saveAsTable(
        f"{SCHEMA}.transaction"
    )


def update_account_balances(spark: SparkSession, valid: DataFrame) -> None:
    """
    Replicates CBTRN02C paragraph 2800-UPDATE-ACCOUNT-REC.

    COBOL logic per transaction:
        ADD DALYTRAN-AMT TO ACCT-CURR-BAL
        IF DALYTRAN-AMT >= 0
            ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT
        ELSE
            ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT

    We aggregate all valid transactions per account and apply as a single
    MERGE operation.
    """
    acct_deltas = valid.groupBy("acct_id").agg(
        F.sum("dalytran_amt").alias("delta_bal"),
        F.sum(
            F.when(F.col("dalytran_amt") >= 0, F.col("dalytran_amt")).otherwise(0)
        ).alias("delta_cyc_credit"),
        F.sum(
            F.when(F.col("dalytran_amt") < 0, F.col("dalytran_amt")).otherwise(0)
        ).alias("delta_cyc_debit"),
    )

    account_table = DeltaTable.forName(spark, f"{SCHEMA}.account")

    account_table.alias("tgt").merge(
        acct_deltas.alias("src"),
        "tgt.acct_id = src.acct_id",
    ).whenMatchedUpdate(
        set={
            "acct_curr_bal": "tgt.acct_curr_bal + src.delta_bal",
            "acct_curr_cyc_credit": "tgt.acct_curr_cyc_credit + src.delta_cyc_credit",
            "acct_curr_cyc_debit": "tgt.acct_curr_cyc_debit + src.delta_cyc_debit",
        }
    ).execute()


def update_tran_cat_balance(spark: SparkSession, valid: DataFrame) -> None:
    """
    Replicates CBTRN02C paragraphs 2700-UPDATE-TCATBAL,
    2700-A-CREATE-TCATBAL-REC, 2700-B-UPDATE-TCATBAL-REC.

    COBOL logic:
        - Read TCATBAL by composite key (acct_id, type_cd, cat_cd)
        - If record exists: ADD DALYTRAN-AMT TO TRAN-CAT-BAL, REWRITE
        - If record not found: INITIALIZE new record, WRITE with amt as balance

    We aggregate valid transactions per (acct_id, type_cd, cat_cd) and MERGE
    into the tran_cat_balance Delta table.
    """
    tcatbal_deltas = valid.groupBy(
        F.col("xref_acct_id").alias("trancat_acct_id"),
        F.col("dalytran_type_cd").alias("trancat_type_cd"),
        F.col("dalytran_cat_cd").alias("trancat_cd"),
    ).agg(
        F.sum("dalytran_amt").alias("delta_bal"),
    )

    tcatbal_table = DeltaTable.forName(spark, f"{SCHEMA}.tran_cat_balance")

    tcatbal_table.alias("tgt").merge(
        tcatbal_deltas.alias("src"),
        """
        tgt.trancat_acct_id = src.trancat_acct_id
        AND tgt.trancat_type_cd = src.trancat_type_cd
        AND tgt.trancat_cd = src.trancat_cd
        """,
    ).whenMatchedUpdate(
        set={"tran_cat_bal": "tgt.tran_cat_bal + src.delta_bal"}
    ).whenNotMatchedInsert(
        values={
            "trancat_acct_id": "src.trancat_acct_id",
            "trancat_type_cd": "src.trancat_type_cd",
            "trancat_cd": "src.trancat_cd",
            "tran_cat_bal": "src.delta_bal",
        }
    ).execute()


def write_rejects(spark: SparkSession, rejects: DataFrame) -> None:
    """
    Replicates CBTRN02C paragraph 2500-WRITE-REJECT-REC.

    Writes rejected transaction records with validation failure reason code
    and description to the daily_rejects Delta table.
    """
    reject_output = rejects.withColumn(
        "reject_timestamp", F.current_timestamp()
    )

    reject_output.write.format("delta").mode("append").saveAsTable(
        f"{SCHEMA}.daily_rejects"
    )


def main() -> None:
    spark = create_spark_session()

    print("CBTRN02C: START OF EXECUTION OF PROGRAM CBTRN02C (PySpark)")

    daily_tran, card_xref, account = load_input_tables(spark)

    total_input = daily_tran.count()
    print(f"CBTRN02C: Daily transactions read: {total_input}")

    valid, rejects = validate_and_split(daily_tran, card_xref, account)

    valid.cache()
    rejects.cache()

    valid_count = valid.count()
    reject_count = rejects.count()

    print(f"CBTRN02C: Transactions validated: {valid_count}")
    print(f"CBTRN02C: Transactions rejected:  {reject_count}")

    if reject_count > 0:
        write_rejects(spark, rejects)
        print("CBTRN02C: Rejected transactions written to DAILY_REJECTS table")

    if valid_count > 0:
        post_transactions(spark, valid)
        print("CBTRN02C: Transactions posted to TRANSACT table")

        update_account_balances(spark, valid)
        print("CBTRN02C: Account balances updated")

        update_tran_cat_balance(spark, valid)
        print("CBTRN02C: Transaction category balances updated")

    valid.unpersist()
    rejects.unpersist()

    print(f"CBTRN02C: TRANSACTIONS PROCESSED :{total_input:09d}")
    print(f"CBTRN02C: TRANSACTIONS REJECTED  :{reject_count:09d}")

    if reject_count > 0:
        print("CBTRN02C: WARNING - Return code 4 (rejections occurred)")

    print("CBTRN02C: END OF EXECUTION OF PROGRAM CBTRN02C (PySpark)")

    spark.stop()


if __name__ == "__main__":
    main()
