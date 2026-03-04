import pytest
from decimal import Decimal
from fastapi import HTTPException

from app.services.card_service import list_cards, get_card_detail, update_card
from app.models.models import Card


class TestListCards:
    def test_list_all(self, db, seed_data):
        result = list_cards(db)
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["has_more"] is False

    def test_filter_by_acct_id(self, db, seed_data):
        result = list_cards(db, acct_id=10000000001)
        assert result["total"] == 1

    def test_filter_by_acct_id_no_match(self, db, seed_data):
        result = list_cards(db, acct_id=99999999999)
        assert result["total"] == 0

    def test_filter_by_card_num(self, db, seed_data):
        result = list_cards(db, card_num="4111")
        assert result["total"] == 1

    def test_pagination(self, db, seed_data):
        for i in range(5):
            card = Card(
                card_num=f"500000000000000{i}",
                acct_id=10000000001,
                cvv_cd=100 + i,
                active_status="Y",
            )
            db.add(card)
        db.commit()
        result = list_cards(db, page=1, page_size=3)
        assert len(result["items"]) == 3
        assert result["has_more"] is True

        result2 = list_cards(db, page=2, page_size=3)
        assert len(result2["items"]) == 3
        assert result2["has_more"] is False


class TestGetCardDetail:
    def test_success(self, db, seed_data):
        result = get_card_detail(db, 10000000001, "4111111111111111")
        assert result["card"].card_num == "4111111111111111"
        assert result["account"].acct_id == 10000000001
        assert result["customer"].first_name == "John"

    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_card_detail(db, 10000000001, "9999999999999999")
        assert exc_info.value.status_code == 404

    def test_wrong_acct_id(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_card_detail(db, 99999999999, "4111111111111111")
        assert exc_info.value.status_code == 404


class TestUpdateCard:
    def test_update_embossed_name(self, db, seed_data):
        result = update_card(db, 10000000001, "4111111111111111", {
            "embossed_name": "JANE DOE",
        })
        assert result["card"].embossed_name == "JANE DOE"

    def test_update_active_status(self, db, seed_data):
        result = update_card(db, 10000000001, "4111111111111111", {
            "active_status": "N",
        })
        assert result["card"].active_status == "N"

    def test_card_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            update_card(db, 10000000001, "9999999999999999", {"active_status": "N"})
        assert exc_info.value.status_code == 404

    def test_no_modification(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            update_card(db, 10000000001, "4111111111111111", {
                "embossed_name": "JOHN DOE",
            })
        assert exc_info.value.status_code == 400
