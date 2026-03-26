import pytest
from decimal import Decimal
from fastapi import HTTPException

from app.services.account_service import get_account_view, update_account


class TestGetAccountView:
    def test_success(self, db, seed_data):
        result = get_account_view(db, 10000000001)
        assert result["account"].acct_id == 10000000001
        assert result["customer"].first_name == "John"

    def test_account_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_account_view(db, 99999999999)
        assert exc_info.value.status_code == 404

    def test_account_without_xref(self, db, seed_data):
        from app.models.models import Account
        orphan = Account(
            acct_id=20000000001,
            active_status="Y",
            curr_bal=Decimal("0"),
            credit_limit=Decimal("1000"),
            cash_credit_limit=Decimal("500"),
        )
        db.add(orphan)
        db.commit()
        result = get_account_view(db, 20000000001)
        assert result["account"].acct_id == 20000000001
        assert result["customer"] is None


class TestUpdateAccount:
    def test_update_account_field(self, db, seed_data):
        result = update_account(db, 10000000001, {"credit_limit": Decimal("8000.00")})
        assert result["account"].credit_limit == Decimal("8000.00")

    def test_update_customer_field(self, db, seed_data):
        result = update_account(db, 10000000001, {"cust_first_name": "Jane"})
        assert result["customer"].first_name == "Jane"

    def test_account_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            update_account(db, 99999999999, {"credit_limit": Decimal("1000")})
        assert exc_info.value.status_code == 404

    def test_no_modification(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            update_account(db, 10000000001, {"credit_limit": seed_data["account"].credit_limit})
        assert exc_info.value.status_code == 400

    def test_update_multiple_fields(self, db, seed_data):
        result = update_account(db, 10000000001, {
            "active_status": "N",
            "cust_last_name": "Smith",
        })
        assert result["account"].active_status == "N"
        assert result["customer"].last_name == "Smith"
