"""
CBSTM03A - Account Statement Generator (PySpark)

Migrated from: app/cbl/CBSTM03A.CBL
COBOL Function: Generate account statements in plain-text and HTML formats
                for each customer/account combination.

Business Logic (exact replica of COBOL):
  1. Read card_xref sequentially (ordered by card_num)
  2. For each card_xref record:
     a. Read customer record from customer table
     b. Read account record from account table
     c. Read all transactions for that card_num from transaction table
  3. Generate a statement per card/account:
     - Header: customer name, address, account info
     - Detail: each transaction (date, id, type, category, source, description, amount)
     - Footer: current balance, credit limit, available credit
  4. COBOL uses a 2D array (WS-TRNX-TABLE) to hold up to 50 transactions
     per statement page - we remove this limitation in PySpark
  5. Output: CSV files for plain-text statements and HTML statements

Note: The original COBOL program has no date filter. It processes ALL
      transactions for each card. In the COBOL JCL flow, a separate step
      (SORT/DFSORT) creates a filtered TRNXFILE extract before CBSTM03A runs.
      In the modernized pipeline, an optional date range parameter is provided
      to replicate this pre-filtering.

Idempotency:
  - This is a read-only report job; it does not write to any Delta table
  - CSV output uses mode("overwrite"), so re-runs replace previous output
  - Safe to run multiple times with the same parameters

Delta tables read: card_xref, customer, account, transaction
Output: CSV files (plain-text statement data + HTML statement files)
"""

import sys
import os
from datetime import datetime
from html import escape as html_escape

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

sys.path.insert(0, "..")
from utils.spark_utils import get_spark_session, get_db_prefix


def _build_html_statement(
    cust_first: str,
    cust_last: str,
    addr_line1: str,
    addr_line2: str,
    addr_line3: str,
    city: str,
    state: str,
    zipcode: str,
    acct_id: int,
    card_num: str,
    stmt_date: str,
    curr_bal: float,
    credit_limit: float,
    transactions: list,
) -> str:
    avail_credit = credit_limit - curr_bal
    name = html_escape(f"{cust_first} {cust_last}".strip())
    lines = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'>",
        f"<title>Statement - Account {acct_id}</title>",
        "<style>",
        "body{font-family:Courier,monospace;margin:20px}",
        "table{border-collapse:collapse;width:100%}",
        "th,td{border:1px solid #333;padding:4px 8px;text-align:left}",
        "th{background:#eee}",
        ".right{text-align:right}",
        ".summary{margin-top:12px}",
        "</style></head><body>",
        f"<h2>CardDemo - Account Statement</h2>",
        f"<p><b>{name}</b><br>",
        f"{html_escape(addr_line1)}<br>",
    ]
    if addr_line2:
        lines.append(f"{html_escape(addr_line2)}<br>")
    if addr_line3:
        lines.append(f"{html_escape(addr_line3)}<br>")
    lines.append(f"{html_escape(city)}, {html_escape(state)} {html_escape(zipcode)}</p>")
    lines.append(f"<p>Account: {acct_id} &nbsp; Card: {html_escape(card_num)} &nbsp; Date: {stmt_date}</p>")
    lines.append("<table><tr>")
    for hdr in ["Date", "Tran ID", "Type", "Category", "Source", "Description", "Amount"]:
        lines.append(f"<th>{hdr}</th>")
    lines.append("</tr>")

    for txn in transactions:
        lines.append("<tr>")
        lines.append(f"<td>{html_escape(str(txn['tran_date']))}</td>")
        lines.append(f"<td>{html_escape(str(txn['tran_id']))}</td>")
        lines.append(f"<td>{html_escape(str(txn['tran_type_cd']))}</td>")
        lines.append(f"<td>{html_escape(str(txn['tran_cat_cd']))}</td>")
        lines.append(f"<td>{html_escape(str(txn['tran_source']))}</td>")
        lines.append(f"<td>{html_escape(str(txn['tran_desc']))}</td>")
        lines.append(f"<td class='right'>{txn['tran_amt']:,.2f}</td>")
        lines.append("</tr>")

    lines.append("</table>")
    lines.append("<div class='summary'>")
    lines.append(f"<p><b>Current Balance:</b> {curr_bal:,.2f}</p>")
    lines.append(f"<p><b>Credit Limit:</b> {credit_limit:,.2f}</p>")
    lines.append(f"<p><b>Available Credit:</b> {avail_credit:,.2f}</p>")
    lines.append("</div></body></html>")
    return "\n".join(lines)


def run(
    start_date: str = "",
    end_date: str = "",
    output_path: str = "",
    catalog: str = "",
    database: str = "carddemo",
) -> dict:
    spark = get_spark_session("CBSTM03A_AccountStatement")
    db = get_db_prefix(catalog, database)
    stmt_date = datetime.now().strftime("%Y-%m-%d")

    if not output_path:
        output_path = f"/tmp/carddemo_statements_{stmt_date}"

    print("START OF EXECUTION OF PROGRAM CBSTM03A")

    xref_df = spark.table(f"{db}.card_xref")
    cust_df = spark.table(f"{db}.customer")
    acct_df = spark.table(f"{db}.account")
    txn_df = spark.table(f"{db}.transaction")

    if start_date and end_date:
        txn_df = txn_df.filter(
            (F.substring(F.col("proc_ts"), 1, 10) >= start_date)
            & (F.substring(F.col("proc_ts"), 1, 10) <= end_date)
        )

    stmt_base = (
        xref_df.alias("xr")
        .join(acct_df.alias("ac"), F.col("xr.acct_id") == F.col("ac.acct_id"), "inner")
        .join(cust_df.alias("cu"), F.col("xr.cust_id") == F.col("cu.cust_id"), "inner")
        .select(
            F.col("xr.card_num"),
            F.col("xr.acct_id"),
            F.col("xr.cust_id"),
            F.col("cu.cust_first_name"),
            F.col("cu.cust_last_name"),
            F.col("cu.cust_addr_line_1"),
            F.col("cu.cust_addr_line_2"),
            F.col("cu.cust_addr_line_3"),
            F.col("cu.cust_addr_city"),
            F.col("cu.cust_addr_state_cd"),
            F.col("cu.cust_addr_zip"),
            F.col("ac.curr_bal"),
            F.col("ac.credit_limit"),
        )
    )

    stmt_records = stmt_base.collect()
    stmt_count = 0
    detail_rows = []
    html_rows = []

    for stmt in stmt_records:
        card_num = stmt["card_num"]
        acct_id = stmt["acct_id"]
        cust_first = stmt["cust_first_name"] or ""
        cust_last = stmt["cust_last_name"] or ""
        curr_bal = float(stmt["curr_bal"] or 0)
        credit_limit = float(stmt["credit_limit"] or 0)

        card_txns = (
            txn_df.filter(F.col("card_num") == card_num)
            .orderBy("orig_ts")
            .select(
                F.substring(F.col("orig_ts"), 1, 10).alias("tran_date"),
                "tran_id",
                "tran_type_cd",
                "tran_cat_cd",
                "tran_source",
                "tran_desc",
                "tran_amt",
            )
            .collect()
        )

        if not card_txns:
            continue

        stmt_count += 1

        txn_list = []
        for txn in card_txns:
            row_dict = {
                "tran_date": txn["tran_date"] or "",
                "tran_id": txn["tran_id"] or "",
                "tran_type_cd": txn["tran_type_cd"] or "",
                "tran_cat_cd": txn["tran_cat_cd"] if txn["tran_cat_cd"] is not None else "",
                "tran_source": txn["tran_source"] or "",
                "tran_desc": txn["tran_desc"] or "",
                "tran_amt": float(txn["tran_amt"] or 0),
            }
            txn_list.append(row_dict)

            detail_rows.append((
                str(acct_id),
                card_num,
                f"{cust_first} {cust_last}".strip(),
                row_dict["tran_date"],
                row_dict["tran_id"],
                row_dict["tran_type_cd"],
                str(row_dict["tran_cat_cd"]),
                row_dict["tran_source"],
                row_dict["tran_desc"],
                row_dict["tran_amt"],
                curr_bal,
                credit_limit,
                credit_limit - curr_bal,
            ))

        html_content = _build_html_statement(
            cust_first=cust_first,
            cust_last=cust_last,
            addr_line1=stmt["cust_addr_line_1"] or "",
            addr_line2=stmt["cust_addr_line_2"] or "",
            addr_line3=stmt["cust_addr_line_3"] or "",
            city=stmt["cust_addr_city"] or "",
            state=stmt["cust_addr_state_cd"] or "",
            zipcode=stmt["cust_addr_zip"] or "",
            acct_id=acct_id,
            card_num=card_num,
            stmt_date=stmt_date,
            curr_bal=curr_bal,
            credit_limit=credit_limit,
            transactions=txn_list,
        )

        html_rows.append((str(acct_id), card_num, html_content))

    if detail_rows:
        detail_schema = (
            "account_id STRING, card_number STRING, customer_name STRING, "
            "tran_date STRING, tran_id STRING, tran_type STRING, tran_category STRING, "
            "tran_source STRING, tran_description STRING, amount DOUBLE, "
            "current_balance DOUBLE, credit_limit DOUBLE, available_credit DOUBLE"
        )
        detail_df = spark.createDataFrame(detail_rows, detail_schema)
        detail_df.coalesce(1).write.option("header", "true").mode("overwrite").csv(
            f"{output_path}/statement_detail"
        )

    if html_rows:
        html_schema = "account_id STRING, card_number STRING, html_content STRING"
        html_df = spark.createDataFrame(html_rows, html_schema)
        html_df.coalesce(1).write.option("header", "true").mode("overwrite").csv(
            f"{output_path}/statement_html"
        )

    print(f"STATEMENTS GENERATED: {stmt_count}")
    print(f"DETAIL ROWS: {len(detail_rows)}")
    print(f"OUTPUT PATH: {output_path}")
    print("END OF EXECUTION OF PROGRAM CBSTM03A")

    return {
        "return_code": 0,
        "statements_generated": stmt_count,
        "detail_rows": len(detail_rows),
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
