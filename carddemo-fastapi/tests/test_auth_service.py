import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from jose import jwt

from app.services.auth_service import (
    create_access_token,
    authenticate_user,
    get_current_user,
    require_admin,
)
from app.config import SECRET_KEY, ALGORITHM
from app.models.models import User


class TestCreateAccessToken:
    def test_returns_valid_jwt(self):
        token = create_access_token({"sub": "ADMIN001", "user_type": "A"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "ADMIN001"
        assert payload["user_type"] == "A"
        assert "exp" in payload

    def test_does_not_mutate_input(self):
        data = {"sub": "USER001"}
        create_access_token(data)
        assert "exp" not in data


class TestAuthenticateUser:
    def test_success(self, db, seed_data):
        result = authenticate_user(db, "ADMIN001", "ADMIN001")
        assert result["user_id"] == "ADMIN001"
        assert result["user_type"] == "A"
        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_user_not_found(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(db, "NOUSER", "password")
        assert exc_info.value.status_code == 404

    def test_wrong_password(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(db, "ADMIN001", "WRONG")
        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    def test_valid_token(self, db, seed_data):
        token = create_access_token({"sub": "ADMIN001"})
        user = get_current_user(token, db)
        assert user.user_id == "ADMIN001"

    def test_invalid_token(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("invalid.token.here", db)
        assert exc_info.value.status_code == 401

    def test_token_missing_sub(self, db, seed_data):
        token = jwt.encode({"data": "no_sub"}, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token, db)
        assert exc_info.value.status_code == 401

    def test_user_deleted_after_token_issued(self, db, seed_data):
        token = create_access_token({"sub": "GHOST01"})
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token, db)
        assert exc_info.value.status_code == 401


class TestRequireAdmin:
    def test_admin_passes(self, db, seed_data):
        require_admin(seed_data["user_admin"])

    def test_regular_user_rejected(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            require_admin(seed_data["user_regular"])
        assert exc_info.value.status_code == 403
