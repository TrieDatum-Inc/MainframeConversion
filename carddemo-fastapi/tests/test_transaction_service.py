import pytest
from decimal import Decimal
from fastapi import HTTPException

from app.services.transaction_service import (
    list_transactions,
    get_transaction_detail,
    add_transaction,
)
from app.models.models import Transaction


class TestListTransactions:
    def test_empty_list(self, db, seed_data):
        result = list_transactions(db)
        assert result["total"] == 0
        assert result["items"] == []

    def test_filter_by_card_num(self, db, seed_data):
        txn = Transaction(
            tran_id="T000000000000001",
            type_cd="01",
            cat_cd=1,
            source="POS",
            description="Test",
            amount=Decimal("50.00"),
            card_num="4111111111111111",
            orig_ts="2025-01-01-12.00.00.000000",
        )
        db.add(txn)
        db.commit()
        result = list_transactions(db, card_num="4111111111111111")
        assert result["total"] == 1

    def test_filter_by_acct_id(self, db, seed_data):
        txn = Transaction(
            tran_id="T000000000000002",
            type_cd="01",
            cat_cd=1,
            source="POS",
            description="Test",
            amount=Decimal("50.00"),
            card_num="4111111111111111",
            orig_ts="2025-01-01-12.00.00.000000",
        )
        db.add(txn)
        db.commit()
        result = list_transactions(db, acct_id=10000000001)
        assert result["total"] == 1

    def test_filter_by_acct_id_no_cards(self, db, seed_data):
        result = list_transactions(db, acct_id=99999999999)
        assert result["total"] == 0
        assert result["items"] == []

    def test_pagination(self, db, seed_data):
        for i in range(15):
            txn = Transaction(
                tran_id=f"T00000000000{i:04d}",
                type_cd="01",
                cat_cd=1,
                source="POS",
                description=f"Txn {i}",
                amount=Decimal("10.00"),
                card_num="4111111111111111",
            )
            db.add(txn)
        db.commit()
        result = list_transactions(db, page=1, page_size=10)
        assert len(result["items"]) == 10
        assert result["has_more"] is True

    def test_filter_by_type_cd(self, db, seed_data):
        txn = Transaction(
            tran_id="T000000000000003",
            type_cd="02",
            cat_cd=1,
            source="POS",
            description="Return",
            amount=Decimal("-20.00"),
            card_num="4111111111111111",
        )
        db.add(txn)
        db.commit()
        result = list_transactions(db, tran_type_cd="02")
        assert result["total"] == 1


class TestGetTransactionDetail:
    def test_found(self, db, seed_data):
        txn = Transaction(
            tran_id="T000000000000010",
            type_cd="01",
            cat_cd=1,
            source="POS",
            description="Test",
            amount=Decimal("50.00"),
            card_num="4111111111111111",
        )
        db.add(txn)
        db.commit()
        result = get_transaction_detail(db, "T000000000000010")
        assert result.tran_id == "T000000000000010"

    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_transaction_detail(db, "NONEXISTENT")
        assert exc_info.value.status_code == 404


class TestAddTransaction:
    def test_success(self, db, seed_data):
        data = {
            "card_num": "4111111111111111",
            "acct_id": 10000000001,
            "type_cd": "01",
            "cat_cd": 1,
            "source": "POS",
            "description": "Purchase at Store",
            "amount": Decimal("100.00"),
        }
        result = add_transaction(db, data)
        assert result.tran_id.startswith("T")
        assert result.amount == Decimal("100.00")

    def test_card_not_found(self, db, seed_data):
        data = {
            "card_num": "9999999999999999",
            "acct_id": 10000000001,
            "type_cd": "01",
            "cat_cd": 1,
            "source": "POS",
            "description": "Test",
            "amount": Decimal("50.00"),
        }
        with pytest.raises(HTTPException) as exc_info:
            add_transaction(db, data)
        assert exc_info.value.status_code == 404

    def test_card_acct_mismatch(self, db, seed_data):
        from app.models.models import Card, CardXref
        card2 = Card(
            card_num="5222222222222222",
            acct_id=10000000001,
            cvv_cd=456,
            active_status="Y",
        )
        xref2 = CardXref(
            card_num="5222222222222222",
            cust_id=1000001,
            acct_id=10000000001,
        )
        db.add_all([card2, xref2])
        db.commit()
        data = {
            "card_num": "5222222222222222",
            "acct_id": 99999999999,
            "type_cd": "01",
            "cat_cd": 1,
            "source": "POS",
            "description": "Test",
            "amount": Decimal("50.00"),
        }
        with pytest.raises(HTTPException) as exc_info:
            add_transaction(db, data)
        assert exc_info.value.status_code == 400

    def test_overlimit(self, db, seed_data):
        data = {
            "card_num": "4111111111111111",
            "acct_id": 10000000001,
            "type_cd": "01",
            "cat_cd": 1,
            "source": "POS",
            "description": "Big purchase",
            "amount": Decimal("50000.00"),
        }
        with pytest.raises(HTTPException) as exc_info:
            add_transaction(db, data)
        assert exc_info.value.status_code == 400
        assert "CREDIT LIMIT" in str(exc_info.value.detail)

    def test_expired_account(self, db, seed_data):
        seed_data["account"].expiration_date = "2020-01-01"
        db.commit()
        data = {
            "card_num": "4111111111111111",
            "acct_id": 10000000001,
            "type_cd": "01",
            "cat_cd": 1,
            "source": "POS",
            "description": "Test",
            "amount": Decimal("50.00"),
        }
        with pytest.raises(HTTPException) as exc_info:
            add_transaction(db, data)
        assert exc_info.value.status_code == 400

    def test_negative_amount_updates_debit(self, db, seed_data):
        data = {
            "card_num": "4111111111111111",
            "acct_id": 10000000001,
            "type_cd": "01",
            "cat_cd": 1,
            "source": "POS",
            "description": "Return",
            "amount": Decimal("-50.00"),
        }
        result = add_transaction(db, data)
        assert result.amount == Decimal("-50.00")
