import pytest
from fastapi import HTTPException

from app.utils.input_validations import (
    validate_optional_acct_id,
    validate_optional_card_num,
    validate_path_variable_acct_id,
    validate_path_variable_card_num,
    validate_query_parma_acct_id,
    validate_query_parma_card_num,
)


class TestValidateOptionalAcctId:
    def test_none_passes(self):
        assert validate_optional_acct_id(None) is None

    def test_valid_11_digits(self):
        assert validate_optional_acct_id("10000000001") == "10000000001"

    def test_invalid_too_short(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_optional_acct_id("12345")
        assert exc_info.value.status_code == 400

    def test_invalid_non_numeric(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_optional_acct_id("1000000000A")
        assert exc_info.value.status_code == 400

    def test_invalid_too_long(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_optional_acct_id("123456789012")
        assert exc_info.value.status_code == 400


class TestValidateOptionalCardNum:
    def test_none_passes(self):
        assert validate_optional_card_num(None) is None

    def test_valid_16_digits(self):
        assert validate_optional_card_num("4111111111111111") == "4111111111111111"

    def test_invalid_too_short(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_optional_card_num("411111111111")
        assert exc_info.value.status_code == 400

    def test_invalid_non_numeric(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_optional_card_num("411111111111111A")
        assert exc_info.value.status_code == 400


class TestValidatePathVariableAcctId:
    def test_valid(self):
        assert validate_path_variable_acct_id("10000000001") == "10000000001"

    def test_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_path_variable_acct_id("123")
        assert exc_info.value.status_code == 400


class TestValidatePathVariableCardNum:
    def test_valid(self):
        assert validate_path_variable_card_num("4111111111111111") == "4111111111111111"

    def test_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_path_variable_card_num("411111")
        assert exc_info.value.status_code == 400


class TestValidateQueryParmaAcctId:
    def test_valid(self):
        assert validate_query_parma_acct_id("10000000001") == "10000000001"

    def test_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_query_parma_acct_id("abc")
        assert exc_info.value.status_code == 400


class TestValidateQueryParmaCardNum:
    def test_valid(self):
        assert validate_query_parma_card_num("4111111111111111") == "4111111111111111"

    def test_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_query_parma_card_num("abc")
        assert exc_info.value.status_code == 400
