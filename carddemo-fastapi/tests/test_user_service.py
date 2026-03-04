import pytest
from fastapi import HTTPException

from app.services.user_service import (
    list_users,
    create_user,
    get_user,
    update_user,
    delete_user,
)


class TestListUsers:
    def test_list_all(self, db, seed_data):
        result = list_users(db)
        assert result["total"] == 2
        assert len(result["items"]) == 2

    def test_filter_by_user_id(self, db, seed_data):
        result = list_users(db, user_id_filter="USER")
        assert result["total"] >= 1

    def test_pagination(self, db, seed_data):
        result = list_users(db, page=1, page_size=1)
        assert len(result["items"]) == 1
        assert result["has_more"] is True


class TestCreateUser:
    def test_success(self, db, seed_data):
        result = create_user(db, {
            "user_id": "NEW001",
            "first_name": "New",
            "last_name": "User",
            "password": "NEW00001",
            "user_type": "U",
        })
        assert result.user_id == "NEW001"
        assert result.user_type == "U"

    def test_duplicate(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            create_user(db, {
                "user_id": "ADMIN001",
                "first_name": "Dup",
                "last_name": "User",
                "password": "PASS",
                "user_type": "U",
            })
        assert exc_info.value.status_code == 409


class TestGetUser:
    def test_found(self, db, seed_data):
        result = get_user(db, "ADMIN001")
        assert result.first_name == "Admin"

    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_user(db, "NOUSER")
        assert exc_info.value.status_code == 404


class TestUpdateUser:
    def test_update_first_name(self, db, seed_data):
        result = update_user(db, "USER0001", {"first_name": "Updated"})
        assert result.first_name == "Updated"

    def test_update_password(self, db, seed_data):
        result = update_user(db, "USER0001", {"password": "NEWPASS"})
        assert result.password == "NEWPASS"

    def test_update_user_type(self, db, seed_data):
        result = update_user(db, "USER0001", {"user_type": "A"})
        assert result.user_type == "A"

    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            update_user(db, "NOUSER", {"first_name": "X"})
        assert exc_info.value.status_code == 404

    def test_no_change(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            update_user(db, "USER0001", {"first_name": "Regular"})
        assert exc_info.value.status_code == 400


class TestDeleteUser:
    def test_success(self, db, seed_data):
        result = delete_user(db, "USER0001")
        assert "deleted" in result["message"]

    def test_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            delete_user(db, "NOUSER")
        assert exc_info.value.status_code == 404
