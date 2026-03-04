import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from jose import jwt

from app.dependencies import get_current_user, require_admin
from app.config import SECRET_KEY, ALGORITHM
from app.models.models import User


class TestGetCurrentUserDep:
    def test_valid_token(self, db, seed_data):
        token = jwt.encode({"sub": "ADMIN001"}, SECRET_KEY, algorithm=ALGORITHM)
        user = get_current_user(token=token, db=db)
        assert user.user_id == "ADMIN001"

    def test_invalid_token(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="bad.token.value", db=db)
        assert exc_info.value.status_code == 401

    def test_missing_sub_in_token(self, db, seed_data):
        token = jwt.encode({"data": "nosub"}, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=db)
        assert exc_info.value.status_code == 401

    def test_user_not_in_db(self, db, seed_data):
        token = jwt.encode({"sub": "GHOST01"}, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=db)
        assert exc_info.value.status_code == 401


class TestRequireAdminDep:
    def test_admin_passes(self, db, seed_data):
        result = require_admin(current_user=seed_data["user_admin"])
        assert result.user_type == "A"

    def test_regular_user_rejected(self, db, seed_data):
        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=seed_data["user_regular"])
        assert exc_info.value.status_code == 403
