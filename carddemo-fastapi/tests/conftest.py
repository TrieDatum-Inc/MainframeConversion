import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

from app.database import Base
from app.models.models import (
    Account, Card, Customer, CardXref, Transaction, User,
    TransactionType, AuthorizationSummary, AuthorizationDetail,
)


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    from sqlalchemy import event, text

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    Base.metadata.create_all(eng)

    with eng.connect() as conn:
        conn.execute(text(
            "DROP TABLE IF EXISTS authorization_details"
        ))
        conn.execute(text(
            "CREATE TABLE authorization_details ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "acct_id BIGINT NOT NULL, "
            "card_num VARCHAR(16) NOT NULL, "
            "auth_date VARCHAR(10), "
            "auth_time VARCHAR(10), "
            "auth_type VARCHAR(2), "
            "auth_id_code VARCHAR(26), "
            "auth_resp_code VARCHAR(2), "
            "auth_resp_reason VARCHAR(4), "
            "transaction_amt NUMERIC(11,2) NOT NULL DEFAULT 0, "
            "approved_amt NUMERIC(11,2) NOT NULL DEFAULT 0, "
            "merchant_category_code VARCHAR(4), "
            "merchant_id VARCHAR(15), "
            "merchant_name VARCHAR(50), "
            "merchant_city VARCHAR(50), "
            "merchant_state VARCHAR(2), "
            "merchant_zip VARCHAR(10), "
            "transaction_id VARCHAR(16), "
            "message_type VARCHAR(4), "
            "message_source VARCHAR(10), "
            "processing_code VARCHAR(2), "
            "card_expiry_date VARCHAR(4), "
            "pos_entry_mode VARCHAR(3), "
            "acqr_country_code VARCHAR(3), "
            "fraud_confirmed VARCHAR(1) DEFAULT ' ', "
            "fraud_rpt_date VARCHAR(10), "
            "match_status VARCHAR(20), "
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        ))
        conn.commit()

    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def seed_data(db):
    account = Account(
        acct_id=10000000001,
        active_status="Y",
        curr_bal=Decimal("500.00"),
        credit_limit=Decimal("5000.00"),
        cash_credit_limit=Decimal("1000.00"),
        open_date="2020-01-01",
        expiration_date="2030-12-31",
        curr_cyc_credit=Decimal("500.00"),
        curr_cyc_debit=Decimal("0.00"),
        group_id="GRP1",
    )
    customer = Customer(
        cust_id=1000001,
        first_name="John",
        middle_name="M",
        last_name="Doe",
        addr_line_1="123 Main St",
        addr_state_cd="CA",
        addr_zip="90210",
    )
    card = Card(
        card_num="4111111111111111",
        acct_id=10000000001,
        cvv_cd=123,
        embossed_name="JOHN DOE",
        expiration_date="2030-12-31",
        active_status="Y",
    )
    xref = CardXref(
        card_num="4111111111111111",
        cust_id=1000001,
        acct_id=10000000001,
    )
    user_admin = User(
        user_id="ADMIN001",
        first_name="Admin",
        last_name="User",
        password="ADMIN001",
        user_type="A",
    )
    user_regular = User(
        user_id="USER0001",
        first_name="Regular",
        last_name="User",
        password="USER0001",
        user_type="U",
    )
    ttype = TransactionType(type_cd="01", type_description="Purchase")
    ttype2 = TransactionType(type_cd="02", type_description="Return")

    db.add_all([account, customer, card, xref, user_admin, user_regular, ttype, ttype2])
    db.commit()

    return {
        "account": account,
        "customer": customer,
        "card": card,
        "xref": xref,
        "user_admin": user_admin,
        "user_regular": user_regular,
        "ttype": ttype,
    }
