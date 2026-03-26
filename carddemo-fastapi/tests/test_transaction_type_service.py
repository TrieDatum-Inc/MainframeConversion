import pytest
from fastapi import HTTPException

from app.services.transaction_type_service import (
    list_transaction_types,
    get_transaction_type,
    create_transaction_type,
    update_transaction_type,
    delete_transaction_type,
)


class TestListTransactionTypes:
    def test_list_all(self, db, seed_data):
        result = list_transaction_types(db)
        assert result["total"] == 2
        assert len(result["items"]) == 2

    def test_filter_by_type_cd(self, db, seed_data):
        result = list_transaction_types(db, type_cd_filter="01")
        assert result["total"] == 1

    def test_filter_by_desc(self, db, seed_data):
        result = list_transaction_types(db, type_desc_filter="Purchase")
        assert result["total"] == 1

    def test_pagination(self, db, seed_data):
        result = list_transaction_types(db, page=1, page_size=1)
        assert len(result["items"]) == 1
        assert result["has_more"] is True


class TestGetTransactionType:
    def test_found(self, db, seed_data):
        result = get_transaction_type(db, "01")
        assert result.type_description == "Purchase"

    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_transaction_type(db, "99")
        assert exc_info.value.status_code == 404


class TestCreateTransactionType:
    def test_success(self, db, seed_data):
        result = create_transaction_type(db, {
            "type_cd": "03",
            "type_description": "Cash Advance",
        })
        assert result.type_cd == "03"
        assert result.type_description == "Cash Advance"

    def test_duplicate(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            create_transaction_type(db, {
                "type_cd": "01",
                "type_description": "Duplicate",
            })
        assert exc_info.value.status_code == 409


class TestUpdateTransactionType:
    def test_success(self, db, seed_data):
        result = update_transaction_type(db, "01", {
            "type_description": "Updated Purchase",
        })
        assert result.type_description == "Updated Purchase"

    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            update_transaction_type(db, "99", {"type_description": "X"})
        assert exc_info.value.status_code == 404

    def test_no_change(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            update_transaction_type(db, "01", {"type_description": "Purchase"})
        assert exc_info.value.status_code == 400


class TestDeleteTransactionType:
    def test_success(self, db, seed_data):
        result = delete_transaction_type(db, "02")
        assert "deleted" in result["message"]
        assert get_transaction_type_safe(db, "02") is None

    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            delete_transaction_type(db, "99")
        assert exc_info.value.status_code == 404


def get_transaction_type_safe(db, type_cd):
    from app.models.models import TransactionType
    return db.query(TransactionType).filter(
        TransactionType.type_cd == type_cd
    ).first()
