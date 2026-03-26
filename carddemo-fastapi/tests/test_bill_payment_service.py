import pytest
from decimal import Decimal
from fastapi import HTTPException

from app.services.bill_payment_service import process_bill_payment
from app.models.models import Transaction


class TestProcessBillPayment:
    def test_success(self, db, seed_data):
        result = process_bill_payment(db, 10000000001)
        assert result["payment_amount"] == Decimal("500.00")
        assert result["new_balance"] == Decimal("0.00")
        assert result["tran_id"].startswith("B")

        txn = db.query(Transaction).filter(Transaction.tran_id == result["tran_id"]).first()
        assert txn is not None
        assert txn.amount == -Decimal("500.00")
        assert txn.source == "BILL-PAY"

    def test_account_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            process_bill_payment(db, 99999999999)
        assert exc_info.value.status_code == 404

    def test_zero_balance(self, db, seed_data):
        seed_data["account"].curr_bal = Decimal("0.00")
        db.commit()
        with pytest.raises(HTTPException) as exc_info:
            process_bill_payment(db, 10000000001)
        assert exc_info.value.status_code == 400

    def test_negative_balance(self, db, seed_data):
        seed_data["account"].curr_bal = Decimal("-50.00")
        db.commit()
        with pytest.raises(HTTPException) as exc_info:
            process_bill_payment(db, 10000000001)
        assert exc_info.value.status_code == 400

    def test_no_xref(self, db, seed_data):
        from app.models.models import Account
        orphan = Account(
            acct_id=20000000001,
            active_status="Y",
            curr_bal=Decimal("100.00"),
            credit_limit=Decimal("1000"),
            cash_credit_limit=Decimal("500"),
        )
        db.add(orphan)
        db.commit()
        with pytest.raises(HTTPException) as exc_info:
            process_bill_payment(db, 20000000001)
        assert exc_info.value.status_code == 404
