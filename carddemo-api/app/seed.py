from decimal import Decimal

from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.models import (
    Account,
    Card,
    CardXref,
    Customer,
    TranCatBalance,
    Transaction,
    TransactionCategory,
    TransactionType,
    User,
)


def seed_database(db: Session) -> None:
    if db.query(User).first():
        return

    users = [
        User(
            id="ADMIN1",
            first_name="Admin",
            last_name="User",
            password_hash=get_password_hash("ADMIN1"),
            user_type="A",
        ),
        User(
            id="USER0001",
            first_name="Regular",
            last_name="User",
            password_hash=get_password_hash("USER0001"),
            user_type="U",
        ),
    ]
    db.add_all(users)

    customers = [
        Customer(
            id=1000001,
            first_name="John",
            middle_name="A",
            last_name="Smith",
            addr_line_1="123 Main Street",
            addr_line_2="Apt 4B",
            addr_state_cd="NY",
            addr_country_cd="US",
            addr_zip="10001",
            phone_num_1="212-555-0101",
            ssn=123456789,
            govt_issued_id="DL12345678",
            dob="1985-03-15",
            eft_account_id="EFT001",
            pri_card_holder_ind="Y",
            fico_credit_score=750,
        ),
        Customer(
            id=1000002,
            first_name="Jane",
            middle_name="B",
            last_name="Doe",
            addr_line_1="456 Oak Avenue",
            addr_state_cd="CA",
            addr_country_cd="US",
            addr_zip="90210",
            phone_num_1="310-555-0202",
            ssn=987654321,
            govt_issued_id="DL87654321",
            dob="1990-07-22",
            eft_account_id="EFT002",
            pri_card_holder_ind="Y",
            fico_credit_score=680,
        ),
        Customer(
            id=1000003,
            first_name="Robert",
            middle_name="C",
            last_name="Johnson",
            addr_line_1="789 Pine Road",
            addr_state_cd="TX",
            addr_country_cd="US",
            addr_zip="73301",
            phone_num_1="512-555-0303",
            ssn=456789123,
            govt_issued_id="DL45678912",
            dob="1978-11-08",
            eft_account_id="EFT003",
            pri_card_holder_ind="Y",
            fico_credit_score=720,
        ),
    ]
    db.add_all(customers)

    accounts = [
        Account(
            id=10000000001,
            active_status="Y",
            curr_bal=Decimal("1500.00"),
            credit_limit=Decimal("5000.00"),
            cash_credit_limit=Decimal("1000.00"),
            open_date="2020-01-15",
            expiration_date="2027-01-15",
            reissue_date="2025-01-15",
            curr_cyc_credit=Decimal("200.00"),
            curr_cyc_debit=Decimal("350.00"),
            addr_zip="10001",
            group_id="GRP001",
        ),
        Account(
            id=10000000002,
            active_status="Y",
            curr_bal=Decimal("3200.50"),
            credit_limit=Decimal("10000.00"),
            cash_credit_limit=Decimal("2000.00"),
            open_date="2019-06-01",
            expiration_date="2026-06-01",
            reissue_date="2024-06-01",
            curr_cyc_credit=Decimal("500.00"),
            curr_cyc_debit=Decimal("800.00"),
            addr_zip="90210",
            group_id="GRP002",
        ),
        Account(
            id=10000000003,
            active_status="Y",
            curr_bal=Decimal("750.25"),
            credit_limit=Decimal("3000.00"),
            cash_credit_limit=Decimal("500.00"),
            open_date="2021-09-10",
            expiration_date="2028-09-10",
            addr_zip="73301",
            group_id="GRP001",
        ),
    ]
    db.add_all(accounts)

    cards = [
        Card(
            card_num="4111111111111111",
            acct_id=10000000001,
            cvv_cd=123,
            embossed_name="JOHN A SMITH",
            expiration_date="2027-01-15",
            active_status="Y",
        ),
        Card(
            card_num="4222222222222222",
            acct_id=10000000002,
            cvv_cd=456,
            embossed_name="JANE B DOE",
            expiration_date="2026-06-01",
            active_status="Y",
        ),
        Card(
            card_num="4333333333333333",
            acct_id=10000000003,
            cvv_cd=789,
            embossed_name="ROBERT C JOHNSON",
            expiration_date="2028-09-10",
            active_status="Y",
        ),
        Card(
            card_num="4111111111112222",
            acct_id=10000000001,
            cvv_cd=321,
            embossed_name="JOHN A SMITH",
            expiration_date="2027-01-15",
            active_status="N",
        ),
    ]
    db.add_all(cards)

    xrefs = [
        CardXref(card_num="4111111111111111", cust_id=1000001, acct_id=10000000001),
        CardXref(card_num="4222222222222222", cust_id=1000002, acct_id=10000000002),
        CardXref(card_num="4333333333333333", cust_id=1000003, acct_id=10000000003),
        CardXref(card_num="4111111111112222", cust_id=1000001, acct_id=10000000001),
    ]
    db.add_all(xrefs)

    tran_types = [
        TransactionType(type_cd="SA", type_desc="Sale"),
        TransactionType(type_cd="RE", type_desc="Return"),
        TransactionType(type_cd="CR", type_desc="Credit"),
        TransactionType(type_cd="DB", type_desc="Debit"),
        TransactionType(type_cd="FE", type_desc="Fee"),
        TransactionType(type_cd="IN", type_desc="Interest"),
    ]
    db.add_all(tran_types)

    tran_categories = [
        TransactionCategory(type_cd="SA", cat_cd=5001, cat_desc="Grocery"),
        TransactionCategory(type_cd="SA", cat_cd=5002, cat_desc="Gas Station"),
        TransactionCategory(type_cd="SA", cat_cd=5003, cat_desc="Restaurant"),
        TransactionCategory(type_cd="SA", cat_cd=5004, cat_desc="Online Shopping"),
        TransactionCategory(type_cd="SA", cat_cd=5005, cat_desc="Travel"),
        TransactionCategory(type_cd="RE", cat_cd=6001, cat_desc="Product Return"),
        TransactionCategory(type_cd="FE", cat_cd=7001, cat_desc="Annual Fee"),
        TransactionCategory(type_cd="FE", cat_cd=7002, cat_desc="Late Payment Fee"),
        TransactionCategory(type_cd="IN", cat_cd=8001, cat_desc="Monthly Interest"),
    ]
    db.add_all(tran_categories)

    transactions = [
        Transaction(
            id="TRN0000000000001",
            type_cd="SA",
            cat_cd=5001,
            source="POS",
            description="Whole Foods Market",
            amount=Decimal("85.42"),
            merchant_id=100001,
            merchant_name="Whole Foods Market",
            merchant_city="New York",
            merchant_zip="10001",
            card_num="4111111111111111",
            orig_ts="2026-02-01-10.30.00.000000",
            proc_ts="2026-02-01-10.30.01.000000",
        ),
        Transaction(
            id="TRN0000000000002",
            type_cd="SA",
            cat_cd=5003,
            source="POS",
            description="The Capital Grille",
            amount=Decimal("156.78"),
            merchant_id=100002,
            merchant_name="The Capital Grille",
            merchant_city="New York",
            merchant_zip="10019",
            card_num="4111111111111111",
            orig_ts="2026-02-03-19.45.00.000000",
            proc_ts="2026-02-03-19.45.01.000000",
        ),
        Transaction(
            id="TRN0000000000003",
            type_cd="SA",
            cat_cd=5004,
            source="ONLINE",
            description="Amazon.com",
            amount=Decimal("299.99"),
            merchant_id=100003,
            merchant_name="Amazon.com Inc",
            merchant_city="Seattle",
            merchant_zip="98101",
            card_num="4222222222222222",
            orig_ts="2026-02-05-14.20.00.000000",
            proc_ts="2026-02-05-14.20.01.000000",
        ),
        Transaction(
            id="TRN0000000000004",
            type_cd="SA",
            cat_cd=5002,
            source="POS",
            description="Shell Gas Station",
            amount=Decimal("45.00"),
            merchant_id=100004,
            merchant_name="Shell Oil",
            merchant_city="Los Angeles",
            merchant_zip="90001",
            card_num="4222222222222222",
            orig_ts="2026-02-07-08.15.00.000000",
            proc_ts="2026-02-07-08.15.01.000000",
        ),
        Transaction(
            id="TRN0000000000005",
            type_cd="SA",
            cat_cd=5005,
            source="ONLINE",
            description="United Airlines",
            amount=Decimal("450.00"),
            merchant_id=100005,
            merchant_name="United Airlines",
            merchant_city="Chicago",
            merchant_zip="60601",
            card_num="4333333333333333",
            orig_ts="2026-02-08-16.00.00.000000",
            proc_ts="2026-02-08-16.00.01.000000",
        ),
        Transaction(
            id="TRN0000000000006",
            type_cd="RE",
            cat_cd=6001,
            source="POS",
            description="Nordstrom Return",
            amount=Decimal("-120.00"),
            merchant_id=100006,
            merchant_name="Nordstrom",
            merchant_city="Austin",
            merchant_zip="73301",
            card_num="4333333333333333",
            orig_ts="2026-02-09-11.30.00.000000",
            proc_ts="2026-02-09-11.30.01.000000",
        ),
    ]
    db.add_all(transactions)

    cat_balances = [
        TranCatBalance(
            acct_id=10000000001,
            type_cd="SA",
            cat_cd=5001,
            balance=Decimal("85.42"),
        ),
        TranCatBalance(
            acct_id=10000000001,
            type_cd="SA",
            cat_cd=5003,
            balance=Decimal("156.78"),
        ),
        TranCatBalance(
            acct_id=10000000002,
            type_cd="SA",
            cat_cd=5004,
            balance=Decimal("299.99"),
        ),
        TranCatBalance(
            acct_id=10000000002,
            type_cd="SA",
            cat_cd=5002,
            balance=Decimal("45.00"),
        ),
        TranCatBalance(
            acct_id=10000000003,
            type_cd="SA",
            cat_cd=5005,
            balance=Decimal("450.00"),
        ),
        TranCatBalance(
            acct_id=10000000003,
            type_cd="RE",
            cat_cd=6001,
            balance=Decimal("-120.00"),
        ),
    ]
    db.add_all(cat_balances)

    db.commit()
