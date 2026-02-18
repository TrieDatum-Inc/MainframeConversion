"""
Seed script to populate the CardDemo MySQL database with sample data.
Mirrors the original mainframe VSAM/DB2 seed data.

Usage:
    poetry run python seed.py
"""

import os
import sys
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base
from app.config import DATABASE_URL
from app.models.models import (
    Account,
    Card,
    Customer,
    CardXref,
    Transaction,
    User,
    TransactionType,
    PendingAuthSummary,
    PendingAuthDetail,
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_users(db):
    users = [
        User(user_id="ADMIN001", first_name="System", last_name="Admin", password="ADMIN001", user_type="A"),
        User(user_id="ADMIN002", first_name="Card", last_name="Admin", password="ADMIN002", user_type="A"),
        User(user_id="USER0001", first_name="John", last_name="Smith", password="USER0001", user_type="U"),
        User(user_id="USER0002", first_name="Jane", last_name="Doe", password="USER0002", user_type="U"),
        User(user_id="USER0003", first_name="Robert", last_name="Johnson", password="USER0003", user_type="U"),
        User(user_id="USER0004", first_name="Maria", last_name="Garcia", password="USER0004", user_type="U"),
        User(user_id="USER0005", first_name="David", last_name="Wilson", password="USER0005", user_type="U"),
    ]
    for u in users:
        db.merge(u)
    db.commit()
    print(f"  Seeded {len(users)} users")


def seed_customers(db):
    customers = [
        Customer(
            cust_id=100000001, first_name="John", middle_name="A", last_name="Smith",
            addr_line_1="123 Main Street", addr_line_2="Apt 4B", addr_line_3="",
            addr_state_cd="NY", addr_country_cd="US", addr_zip="10001",
            phone_num_1="212-555-0101", phone_num_2="917-555-0101",
            ssn=123456789, govt_issued_id="DL-NY-12345678",
            dob_yyyymmdd="1985-05-15", eft_account_id="EFT0000001",
            pri_card_holder_ind="Y", fico_credit_score=750,
        ),
        Customer(
            cust_id=100000002, first_name="Jane", middle_name="B", last_name="Doe",
            addr_line_1="456 Oak Avenue", addr_line_2="Suite 200", addr_line_3="",
            addr_state_cd="CA", addr_country_cd="US", addr_zip="90210",
            phone_num_1="310-555-0202", phone_num_2="213-555-0202",
            ssn=987654321, govt_issued_id="DL-CA-87654321",
            dob_yyyymmdd="1990-08-22", eft_account_id="EFT0000002",
            pri_card_holder_ind="Y", fico_credit_score=680,
        ),
        Customer(
            cust_id=100000003, first_name="Robert", middle_name="C", last_name="Johnson",
            addr_line_1="789 Pine Road", addr_line_2="", addr_line_3="",
            addr_state_cd="TX", addr_country_cd="US", addr_zip="75201",
            phone_num_1="214-555-0303", phone_num_2="",
            ssn=456789123, govt_issued_id="DL-TX-45678912",
            dob_yyyymmdd="1978-12-01", eft_account_id="EFT0000003",
            pri_card_holder_ind="Y", fico_credit_score=720,
        ),
        Customer(
            cust_id=100000004, first_name="Maria", middle_name="D", last_name="Garcia",
            addr_line_1="321 Elm Street", addr_line_2="Floor 3", addr_line_3="",
            addr_state_cd="FL", addr_country_cd="US", addr_zip="33101",
            phone_num_1="305-555-0404", phone_num_2="786-555-0404",
            ssn=789123456, govt_issued_id="DL-FL-78912345",
            dob_yyyymmdd="1982-03-18", eft_account_id="EFT0000004",
            pri_card_holder_ind="Y", fico_credit_score=790,
        ),
        Customer(
            cust_id=100000005, first_name="David", middle_name="E", last_name="Wilson",
            addr_line_1="654 Maple Lane", addr_line_2="", addr_line_3="",
            addr_state_cd="IL", addr_country_cd="US", addr_zip="60601",
            phone_num_1="312-555-0505", phone_num_2="",
            ssn=321654987, govt_issued_id="DL-IL-32165498",
            dob_yyyymmdd="1995-07-09", eft_account_id="EFT0000005",
            pri_card_holder_ind="Y", fico_credit_score=650,
        ),
    ]
    for c in customers:
        db.merge(c)
    db.commit()
    print(f"  Seeded {len(customers)} customers")


def seed_accounts(db):
    accounts = [
        Account(
            acct_id=10000000001, active_status="Y",
            curr_bal=Decimal("1250.75"), credit_limit=Decimal("5000.00"),
            cash_credit_limit=Decimal("1500.00"),
            open_date="2020-01-15", expiration_date="2026-01-15",
            reissue_date="2024-01-15",
            curr_cyc_credit=Decimal("500.00"), curr_cyc_debit=Decimal("250.75"),
            addr_zip="10001", group_id="GRP001",
        ),
        Account(
            acct_id=10000000002, active_status="Y",
            curr_bal=Decimal("3456.89"), credit_limit=Decimal("10000.00"),
            cash_credit_limit=Decimal("3000.00"),
            open_date="2019-06-20", expiration_date="2025-06-20",
            reissue_date="2023-06-20",
            curr_cyc_credit=Decimal("2000.00"), curr_cyc_debit=Decimal("1456.89"),
            addr_zip="90210", group_id="GRP002",
        ),
        Account(
            acct_id=10000000003, active_status="Y",
            curr_bal=Decimal("750.00"), credit_limit=Decimal("7500.00"),
            cash_credit_limit=Decimal("2500.00"),
            open_date="2021-03-10", expiration_date="2027-03-10",
            reissue_date="2025-03-10",
            curr_cyc_credit=Decimal("1000.00"), curr_cyc_debit=Decimal("750.00"),
            addr_zip="75201", group_id="GRP001",
        ),
        Account(
            acct_id=10000000004, active_status="Y",
            curr_bal=Decimal("0.00"), credit_limit=Decimal("15000.00"),
            cash_credit_limit=Decimal("5000.00"),
            open_date="2018-11-05", expiration_date="2026-11-05",
            reissue_date="2024-11-05",
            curr_cyc_credit=Decimal("0.00"), curr_cyc_debit=Decimal("0.00"),
            addr_zip="33101", group_id="GRP003",
        ),
        Account(
            acct_id=10000000005, active_status="N",
            curr_bal=Decimal("5678.23"), credit_limit=Decimal("3000.00"),
            cash_credit_limit=Decimal("1000.00"),
            open_date="2022-09-01", expiration_date="2025-09-01",
            reissue_date="",
            curr_cyc_credit=Decimal("100.00"), curr_cyc_debit=Decimal("5578.23"),
            addr_zip="60601", group_id="GRP002",
        ),
    ]
    for a in accounts:
        db.merge(a)
    db.commit()
    print(f"  Seeded {len(accounts)} accounts")


def seed_cards(db):
    cards = [
        Card(card_num="4111111111111111", acct_id=10000000001, cvv_cd=123,
             embossed_name="JOHN A SMITH", expiration_date="2026-01-15", active_status="Y"),
        Card(card_num="4222222222222222", acct_id=10000000001, cvv_cd=456,
             embossed_name="JOHN A SMITH", expiration_date="2026-01-15", active_status="Y"),
        Card(card_num="5333333333333333", acct_id=10000000002, cvv_cd=789,
             embossed_name="JANE B DOE", expiration_date="2025-06-20", active_status="Y"),
        Card(card_num="5444444444444444", acct_id=10000000003, cvv_cd=321,
             embossed_name="ROBERT C JOHNSON", expiration_date="2027-03-10", active_status="Y"),
        Card(card_num="4555555555555555", acct_id=10000000004, cvv_cd=654,
             embossed_name="MARIA D GARCIA", expiration_date="2026-11-05", active_status="Y"),
        Card(card_num="4666666666666666", acct_id=10000000005, cvv_cd=987,
             embossed_name="DAVID E WILSON", expiration_date="2025-09-01", active_status="N"),
    ]
    for c in cards:
        db.merge(c)
    db.commit()
    print(f"  Seeded {len(cards)} cards")


def seed_card_xref(db):
    xrefs = [
        CardXref(card_num="4111111111111111", cust_id=100000001, acct_id=10000000001),
        CardXref(card_num="4222222222222222", cust_id=100000001, acct_id=10000000001),
        CardXref(card_num="5333333333333333", cust_id=100000002, acct_id=10000000002),
        CardXref(card_num="5444444444444444", cust_id=100000003, acct_id=10000000003),
        CardXref(card_num="4555555555555555", cust_id=100000004, acct_id=10000000004),
        CardXref(card_num="4666666666666666", cust_id=100000005, acct_id=10000000005),
    ]
    for x in xrefs:
        db.merge(x)
    db.commit()
    print(f"  Seeded {len(xrefs)} card cross-references")


def seed_transactions(db):
    transactions = [
        Transaction(
            tran_id="T000000000000001", type_cd="01", cat_cd=5411, source="POS",
            description="Grocery Store Purchase", amount=Decimal("125.50"),
            merchant_id=900000001, merchant_name="Fresh Foods Market",
            merchant_city="New York", merchant_zip="10001",
            card_num="4111111111111111",
            orig_ts="2025-01-15-10.30.00.000000", proc_ts="2025-01-15-10.30.01.000000",
        ),
        Transaction(
            tran_id="T000000000000002", type_cd="01", cat_cd=5812, source="POS",
            description="Restaurant Dinner", amount=Decimal("85.20"),
            merchant_id=900000002, merchant_name="Italian Kitchen",
            merchant_city="New York", merchant_zip="10002",
            card_num="4111111111111111",
            orig_ts="2025-01-16-19.15.00.000000", proc_ts="2025-01-16-19.15.01.000000",
        ),
        Transaction(
            tran_id="T000000000000003", type_cd="02", cat_cd=5912, source="ONLINE",
            description="Online Pharmacy Order", amount=Decimal("45.99"),
            merchant_id=900000003, merchant_name="Health Plus Pharmacy",
            merchant_city="Los Angeles", merchant_zip="90210",
            card_num="5333333333333333",
            orig_ts="2025-01-17-14.00.00.000000", proc_ts="2025-01-17-14.00.01.000000",
        ),
        Transaction(
            tran_id="T000000000000004", type_cd="01", cat_cd=5541, source="POS",
            description="Gas Station Fuel", amount=Decimal("67.80"),
            merchant_id=900000004, merchant_name="Quick Gas Station",
            merchant_city="Dallas", merchant_zip="75201",
            card_num="5444444444444444",
            orig_ts="2025-01-18-08.45.00.000000", proc_ts="2025-01-18-08.45.01.000000",
        ),
        Transaction(
            tran_id="T000000000000005", type_cd="03", cat_cd=5311, source="POS",
            description="Department Store Purchase", amount=Decimal("299.99"),
            merchant_id=900000005, merchant_name="Grand Department Store",
            merchant_city="Miami", merchant_zip="33101",
            card_num="4555555555555555",
            orig_ts="2025-01-19-12.30.00.000000", proc_ts="2025-01-19-12.30.01.000000",
        ),
        Transaction(
            tran_id="T000000000000006", type_cd="01", cat_cd=4121, source="ONLINE",
            description="Taxi Ride", amount=Decimal("32.50"),
            merchant_id=900000006, merchant_name="City Taxi Service",
            merchant_city="New York", merchant_zip="10003",
            card_num="4222222222222222",
            orig_ts="2025-01-20-09.00.00.000000", proc_ts="2025-01-20-09.00.01.000000",
        ),
        Transaction(
            tran_id="T000000000000007", type_cd="02", cat_cd=5732, source="ONLINE",
            description="Electronics Purchase", amount=Decimal("599.00"),
            merchant_id=900000007, merchant_name="Tech World Online",
            merchant_city="San Francisco", merchant_zip="94102",
            card_num="5333333333333333",
            orig_ts="2025-01-21-16.20.00.000000", proc_ts="2025-01-21-16.20.01.000000",
        ),
        Transaction(
            tran_id="T000000000000008", type_cd="01", cat_cd=5814, source="POS",
            description="Fast Food Lunch", amount=Decimal("12.75"),
            merchant_id=900000008, merchant_name="Burger Place",
            merchant_city="Dallas", merchant_zip="75202",
            card_num="5444444444444444",
            orig_ts="2025-01-22-12.00.00.000000", proc_ts="2025-01-22-12.00.01.000000",
        ),
        Transaction(
            tran_id="T000000000000009", type_cd="04", cat_cd=6011, source="ATM",
            description="Cash Advance", amount=Decimal("200.00"),
            merchant_id=900000009, merchant_name="Bank ATM Downtown",
            merchant_city="Chicago", merchant_zip="60601",
            card_num="4666666666666666",
            orig_ts="2025-01-23-15.30.00.000000", proc_ts="2025-01-23-15.30.01.000000",
        ),
        Transaction(
            tran_id="T000000000000010", type_cd="01", cat_cd=5411, source="POS",
            description="Supermarket Weekly Shopping", amount=Decimal("187.35"),
            merchant_id=900000010, merchant_name="Mega Supermarket",
            merchant_city="New York", merchant_zip="10004",
            card_num="4111111111111111",
            orig_ts="2025-01-24-11.15.00.000000", proc_ts="2025-01-24-11.15.01.000000",
        ),
    ]
    for t in transactions:
        db.merge(t)
    db.commit()
    print(f"  Seeded {len(transactions)} transactions")


def seed_transaction_types(db):
    types = [
        TransactionType(type_cd="01", type_description="Purchase"),
        TransactionType(type_cd="02", type_description="Return/Refund"),
        TransactionType(type_cd="03", type_description="Balance Transfer"),
        TransactionType(type_cd="04", type_description="Cash Advance"),
        TransactionType(type_cd="05", type_description="Payment"),
        TransactionType(type_cd="06", type_description="Fee"),
        TransactionType(type_cd="07", type_description="Interest Charge"),
        TransactionType(type_cd="08", type_description="Adjustment"),
        TransactionType(type_cd="09", type_description="Reversal"),
        TransactionType(type_cd="10", type_description="Credit Voucher"),
    ]
    for t in types:
        db.merge(t)
    db.commit()
    print(f"  Seeded {len(types)} transaction types")


def seed_pending_auth_summary(db):
    summaries = [
        PendingAuthSummary(
            acct_id=10000000001, cust_id=100000001,
            credit_limit=Decimal("5000.00"), cash_limit=Decimal("1500.00"),
            credit_balance=Decimal("1250.75"), cash_balance=Decimal("0.00"),
            approved_auth_cnt=3, approved_auth_amt=Decimal("350.00"),
            declined_auth_cnt=1, declined_auth_amt=Decimal("6000.00"),
        ),
        PendingAuthSummary(
            acct_id=10000000002, cust_id=100000002,
            credit_limit=Decimal("10000.00"), cash_limit=Decimal("3000.00"),
            credit_balance=Decimal("3456.89"), cash_balance=Decimal("0.00"),
            approved_auth_cnt=5, approved_auth_amt=Decimal("1200.00"),
            declined_auth_cnt=0, declined_auth_amt=Decimal("0.00"),
        ),
    ]
    for s in summaries:
        db.merge(s)
    db.commit()
    print(f"  Seeded {len(summaries)} pending auth summaries")


def seed_pending_auth_details(db):
    details = [
        PendingAuthDetail(
            acct_id=10000000001, card_num="4111111111111111",
            auth_date="2025-01-25", auth_time="10:30:00",
            auth_type="01", auth_id_code="AUTH000001",
            auth_resp_code="00", auth_resp_reason="0000",
            transaction_amt=Decimal("150.00"), approved_amt=Decimal("150.00"),
            merchant_category_code="5411", merchant_id="900000001",
            merchant_name="Fresh Foods Market", merchant_city="New York",
            merchant_state="NY", merchant_zip="10001",
            transaction_id="T000000000000011", message_type="0100",
            message_source="POS", processing_code="00",
            card_expiry_date="2601", pos_entry_mode="051",
            acqr_country_code="840",
            fraud_confirmed=" ", fraud_rpt_date="", match_status="PENDING",
        ),
        PendingAuthDetail(
            acct_id=10000000001, card_num="4111111111111111",
            auth_date="2025-01-25", auth_time="14:15:00",
            auth_type="01", auth_id_code="AUTH000002",
            auth_resp_code="00", auth_resp_reason="0000",
            transaction_amt=Decimal("100.00"), approved_amt=Decimal("100.00"),
            merchant_category_code="5812", merchant_id="900000002",
            merchant_name="Italian Kitchen", merchant_city="New York",
            merchant_state="NY", merchant_zip="10002",
            transaction_id="T000000000000012", message_type="0100",
            message_source="POS", processing_code="00",
            card_expiry_date="2601", pos_entry_mode="051",
            acqr_country_code="840",
            fraud_confirmed=" ", fraud_rpt_date="", match_status="PENDING",
        ),
        PendingAuthDetail(
            acct_id=10000000001, card_num="4222222222222222",
            auth_date="2025-01-26", auth_time="09:00:00",
            auth_type="01", auth_id_code="AUTH000003",
            auth_resp_code="00", auth_resp_reason="0000",
            transaction_amt=Decimal("100.00"), approved_amt=Decimal("100.00"),
            merchant_category_code="4121", merchant_id="900000006",
            merchant_name="City Taxi Service", merchant_city="New York",
            merchant_state="NY", merchant_zip="10003",
            transaction_id="T000000000000013", message_type="0100",
            message_source="POS", processing_code="00",
            card_expiry_date="2601", pos_entry_mode="051",
            acqr_country_code="840",
            fraud_confirmed=" ", fraud_rpt_date="", match_status="PENDING",
        ),
        PendingAuthDetail(
            acct_id=10000000001, card_num="4111111111111111",
            auth_date="2025-01-26", auth_time="16:00:00",
            auth_type="01", auth_id_code="AUTH000004",
            auth_resp_code="05", auth_resp_reason="4100",
            transaction_amt=Decimal("6000.00"), approved_amt=Decimal("0.00"),
            merchant_category_code="5732", merchant_id="900000007",
            merchant_name="Tech World Online", merchant_city="San Francisco",
            merchant_state="CA", merchant_zip="94102",
            transaction_id="T000000000000014", message_type="0100",
            message_source="ONLINE", processing_code="00",
            card_expiry_date="2601", pos_entry_mode="010",
            acqr_country_code="840",
            fraud_confirmed=" ", fraud_rpt_date="", match_status="AUTH-DECLINED",
        ),
        PendingAuthDetail(
            acct_id=10000000002, card_num="5333333333333333",
            auth_date="2025-01-27", auth_time="11:00:00",
            auth_type="01", auth_id_code="AUTH000005",
            auth_resp_code="00", auth_resp_reason="0000",
            transaction_amt=Decimal("500.00"), approved_amt=Decimal("500.00"),
            merchant_category_code="5311", merchant_id="900000005",
            merchant_name="Grand Department Store", merchant_city="Los Angeles",
            merchant_state="CA", merchant_zip="90210",
            transaction_id="T000000000000015", message_type="0100",
            message_source="POS", processing_code="00",
            card_expiry_date="2506", pos_entry_mode="051",
            acqr_country_code="840",
            fraud_confirmed="F", fraud_rpt_date="2025-01-28", match_status="PENDING",
        ),
    ]
    for d in details:
        db.add(d)
    db.commit()
    print(f"  Seeded {len(details)} pending auth details")


def main():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.\n")

    db = SessionLocal()
    try:
        print("Seeding data...")
        seed_users(db)
        seed_customers(db)
        seed_accounts(db)
        seed_cards(db)
        seed_card_xref(db)
        seed_transactions(db)
        seed_transaction_types(db)
        seed_pending_auth_summary(db)
        seed_pending_auth_details(db)
        print("\nSeed completed successfully!")
        print("\nSample credentials:")
        print("  Admin: user_id=ADMIN001, password=ADMIN001")
        print("  User:  user_id=USER0001, password=USER0001")
        print("\nSample data:")
        print("  Accounts: 10000000001 through 10000000005")
        print("  Cards: 4111111111111111, 5333333333333333, etc.")
        print("  Transactions: T000000000000001 through T000000000000010")
    finally:
        db.close()


if __name__ == "__main__":
    main()
