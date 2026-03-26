import pytest
from decimal import Decimal
from fastapi import HTTPException

from app.services.authorization_service import (
    process_authorization,
    _build_decline_response,
    get_auth_summary,
    get_auth_detail,
    toggle_fraud_flag,
)
from app.models.models import AuthorizationSummary, AuthorizationDetail


class TestBuildDeclineResponse:
    def test_returns_correct_fields(self):
        result = _build_decline_response(
            "4111111111111111", "TXN001", "12:00:00",
            "05", "3100", Decimal("0"),
        )
        assert result["card_num"] == "4111111111111111"
        assert result["transaction_id"] == "TXN001"
        assert result["auth_resp_code"] == "05"
        assert result["auth_resp_reason"] == "3100"
        assert result["approved_amt"] == Decimal("0")


class TestProcessAuthorization:
    def test_card_not_found(self, db, seed_data):
        result = process_authorization(db, {
            "card_num": "9999999999999999",
            "transaction_amt": 100,
            "auth_time": "12:00:00",
        })
        assert result["auth_resp_code"] == "05"
        assert result["auth_resp_reason"] == "3100"

    def test_approved(self, db, seed_data):
        result = process_authorization(db, {
            "card_num": "4111111111111111",
            "transaction_amt": 100,
            "auth_time": "12:00:00",
            "transaction_id": "TXN001",
        })
        assert result["auth_resp_code"] == "00"
        assert result["approved_amt"] == Decimal("100")

    def test_insufficient_funds(self, db, seed_data):
        result = process_authorization(db, {
            "card_num": "4111111111111111",
            "transaction_amt": 50000,
            "auth_time": "12:00:00",
        })
        assert result["auth_resp_code"] == "05"
        assert result["auth_resp_reason"] == "4100"

    def test_account_closed(self, db, seed_data):
        seed_data["account"].active_status = "N"
        db.commit()
        result = process_authorization(db, {
            "card_num": "4111111111111111",
            "transaction_amt": 100,
            "auth_time": "12:00:00",
        })
        assert result["auth_resp_code"] == "05"

    def test_creates_auth_summary_and_detail(self, db, seed_data):
        process_authorization(db, {
            "card_num": "4111111111111111",
            "transaction_amt": 100,
            "auth_time": "12:00:00",
            "auth_date": "2025-01-01",
        })
        summary = db.query(AuthorizationSummary).filter(
            AuthorizationSummary.acct_id == 10000000001
        ).first()
        assert summary is not None
        assert summary.approved_auth_cnt == 1

        details = db.query(AuthorizationDetail).all()
        assert len(details) == 1


class TestGetAuthSummary:
    def test_account_not_in_xref(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_auth_summary(db, 99999999999)
        assert exc_info.value.status_code == 404

    def test_success_no_prior_auths(self, db, seed_data):
        result = get_auth_summary(db, 10000000001)
        assert result["acct_id"] == 10000000001
        assert result["approved_count"] == 0
        assert result["authorizations"] == []

    def test_pagination(self, db, seed_data):
        summary = AuthorizationSummary(
            acct_id=10000000001,
            cust_id=1000001,
            credit_limit=Decimal("5000"),
            cash_limit=Decimal("1000"),
            credit_balance=Decimal("0"),
            cash_balance=Decimal("0"),
            approved_auth_cnt=0,
            approved_auth_amt=Decimal("0"),
            declined_auth_cnt=0,
            declined_auth_amt=Decimal("0"),
        )
        db.add(summary)
        db.flush()

        for i in range(7):
            detail = AuthorizationDetail(
                acct_id=10000000001,
                card_num="4111111111111111",
                transaction_amt=Decimal("100"),
                approved_amt=Decimal("100"),
                match_status="PENDING",
            )
            db.add(detail)
        db.commit()

        result = get_auth_summary(db, 10000000001, page=1, page_size=5)
        assert len(result["authorizations"]) == 5
        assert result["has_more"] is True


class TestGetAuthDetail:
    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_auth_detail(db, 99999)
        assert exc_info.value.status_code == 404

    def test_found(self, db, seed_data):
        summary = AuthorizationSummary(
            acct_id=10000000001,
            cust_id=1000001,
            credit_limit=Decimal("5000"),
            cash_limit=Decimal("1000"),
            credit_balance=Decimal("0"),
            cash_balance=Decimal("0"),
            approved_auth_cnt=0,
            approved_auth_amt=Decimal("0"),
            declined_auth_cnt=0,
            declined_auth_amt=Decimal("0"),
        )
        db.add(summary)
        db.flush()
        detail = AuthorizationDetail(
            acct_id=10000000001,
            card_num="4111111111111111",
            transaction_amt=Decimal("100"),
            approved_amt=Decimal("100"),
            match_status="PENDING",
        )
        db.add(detail)
        db.commit()
        result = get_auth_detail(db, detail.id)
        assert result.card_num == "4111111111111111"


class TestToggleFraudFlag:
    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            toggle_fraud_flag(db, 99999)
        assert exc_info.value.status_code == 404

    def test_set_fraud(self, db, seed_data):
        summary = AuthorizationSummary(
            acct_id=10000000001,
            cust_id=1000001,
            credit_limit=Decimal("5000"),
            cash_limit=Decimal("1000"),
            credit_balance=Decimal("0"),
            cash_balance=Decimal("0"),
            approved_auth_cnt=0,
            approved_auth_amt=Decimal("0"),
            declined_auth_cnt=0,
            declined_auth_amt=Decimal("0"),
        )
        db.add(summary)
        db.flush()
        detail = AuthorizationDetail(
            acct_id=10000000001,
            card_num="4111111111111111",
            transaction_amt=Decimal("100"),
            approved_amt=Decimal("100"),
            fraud_confirmed=" ",
            match_status="PENDING",
        )
        db.add(detail)
        db.commit()
        result = toggle_fraud_flag(db, detail.id)
        assert result["fraud_confirmed"] == "F"
        assert result["message"] == "Fraud flag set"

    def test_remove_fraud(self, db, seed_data):
        summary = AuthorizationSummary(
            acct_id=10000000001,
            cust_id=1000001,
            credit_limit=Decimal("5000"),
            cash_limit=Decimal("1000"),
            credit_balance=Decimal("0"),
            cash_balance=Decimal("0"),
            approved_auth_cnt=0,
            approved_auth_amt=Decimal("0"),
            declined_auth_cnt=0,
            declined_auth_amt=Decimal("0"),
        )
        db.add(summary)
        db.flush()
        detail = AuthorizationDetail(
            acct_id=10000000001,
            card_num="4111111111111111",
            transaction_amt=Decimal("100"),
            approved_amt=Decimal("100"),
            fraud_confirmed="F",
            fraud_rpt_date="2025-01-01",
            match_status="PENDING",
        )
        db.add(detail)
        db.commit()
        result = toggle_fraud_flag(db, detail.id)
        assert result["fraud_confirmed"] == " "
        assert result["message"] == "Fraud flag removed"
