from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(25))
    middle_name: Mapped[str] = mapped_column(String(25), default="")
    last_name: Mapped[str] = mapped_column(String(25))
    addr_line_1: Mapped[str] = mapped_column(String(50), default="")
    addr_line_2: Mapped[str] = mapped_column(String(50), default="")
    addr_line_3: Mapped[str] = mapped_column(String(50), default="")
    addr_state_cd: Mapped[str] = mapped_column(String(2), default="")
    addr_country_cd: Mapped[str] = mapped_column(String(3), default="")
    addr_zip: Mapped[str] = mapped_column(String(10), default="")
    phone_num_1: Mapped[str] = mapped_column(String(15), default="")
    phone_num_2: Mapped[str] = mapped_column(String(15), default="")
    ssn: Mapped[int] = mapped_column(Integer)
    govt_issued_id: Mapped[str] = mapped_column(String(20), default="")
    dob: Mapped[str] = mapped_column(String(10), default="")
    eft_account_id: Mapped[str] = mapped_column(String(10), default="")
    pri_card_holder_ind: Mapped[str] = mapped_column(String(1), default="Y")
    fico_credit_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    xrefs: Mapped[list["CardXref"]] = relationship(back_populates="customer")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    active_status: Mapped[str] = mapped_column(String(1), default="Y")
    curr_bal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00")
    )
    cash_credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00")
    )
    open_date: Mapped[str] = mapped_column(String(10), default="")
    expiration_date: Mapped[str] = mapped_column(String(10), default="")
    reissue_date: Mapped[str] = mapped_column(String(10), default="")
    curr_cyc_credit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00")
    )
    curr_cyc_debit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00")
    )
    addr_zip: Mapped[str] = mapped_column(String(10), default="")
    group_id: Mapped[str] = mapped_column(String(10), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    cards: Mapped[list["Card"]] = relationship(back_populates="account")
    xrefs: Mapped[list["CardXref"]] = relationship(back_populates="account")


class Card(Base):
    __tablename__ = "cards"

    card_num: Mapped[str] = mapped_column(String(16), primary_key=True)
    acct_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), index=True
    )
    cvv_cd: Mapped[int] = mapped_column(Integer, default=0)
    embossed_name: Mapped[str] = mapped_column(String(50), default="")
    expiration_date: Mapped[str] = mapped_column(String(10), default="")
    active_status: Mapped[str] = mapped_column(String(1), default="Y")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    account: Mapped["Account"] = relationship(back_populates="cards")


class CardXref(Base):
    __tablename__ = "card_xrefs"

    card_num: Mapped[str] = mapped_column(String(16), primary_key=True)
    cust_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("customers.id"), index=True
    )
    acct_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), index=True
    )

    customer: Mapped["Customer"] = relationship(back_populates="xrefs")
    account: Mapped["Account"] = relationship(back_populates="xrefs")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    type_cd: Mapped[str] = mapped_column(String(2), default="")
    cat_cd: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(10), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    amount: Mapped[Decimal] = mapped_column(Numeric(11, 2), default=Decimal("0.00"))
    merchant_id: Mapped[int] = mapped_column(Integer, default=0)
    merchant_name: Mapped[str] = mapped_column(String(50), default="")
    merchant_city: Mapped[str] = mapped_column(String(50), default="")
    merchant_zip: Mapped[str] = mapped_column(String(10), default="")
    card_num: Mapped[str] = mapped_column(String(16), index=True)
    orig_ts: Mapped[str] = mapped_column(String(26), default="")
    proc_ts: Mapped[str] = mapped_column(String(26), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_transactions_card_orig", "card_num", "orig_ts"),)


class TransactionType(Base):
    __tablename__ = "transaction_types"

    type_cd: Mapped[str] = mapped_column(String(2), primary_key=True)
    type_desc: Mapped[str] = mapped_column(String(50), default="")


class TransactionCategory(Base):
    __tablename__ = "transaction_categories"

    type_cd: Mapped[str] = mapped_column(String(2), primary_key=True)
    cat_cd: Mapped[int] = mapped_column(Integer, primary_key=True)
    cat_desc: Mapped[str] = mapped_column(String(50), default="")


class TranCatBalance(Base):
    __tablename__ = "tran_cat_balances"

    acct_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), primary_key=True
    )
    type_cd: Mapped[str] = mapped_column(String(2), primary_key=True)
    cat_cd: Mapped[int] = mapped_column(Integer, primary_key=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(11, 2), default=Decimal("0.00"))


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(20), default="")
    last_name: Mapped[str] = mapped_column(String(20), default="")
    password_hash: Mapped[str] = mapped_column(String(128))
    user_type: Mapped[str] = mapped_column(String(1), default="U")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
