import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jobs.cbtrn02c_daily_transaction_posting_rec import (
    REASON_INVALID_CARD,
    REASON_ACCOUNT_NOT_FOUND,
    REASON_OVERLIMIT,
    REASON_EXPIRED,
    REASON_DESCRIPTIONS,
)


class TestReasonCodes:
    def test_invalid_card_code(self):
        assert REASON_INVALID_CARD == 100

    def test_account_not_found_code(self):
        assert REASON_ACCOUNT_NOT_FOUND == 101

    def test_overlimit_code(self):
        assert REASON_OVERLIMIT == 102

    def test_expired_code(self):
        assert REASON_EXPIRED == 103


class TestReasonDescriptions:
    def test_all_codes_have_descriptions(self):
        for code in [100, 101, 102, 103]:
            assert code in REASON_DESCRIPTIONS

    def test_invalid_card_desc(self):
        assert REASON_DESCRIPTIONS[100] == "INVALID CARD NUMBER FOUND"

    def test_account_not_found_desc(self):
        assert REASON_DESCRIPTIONS[101] == "ACCOUNT RECORD NOT FOUND"

    def test_overlimit_desc(self):
        assert REASON_DESCRIPTIONS[102] == "OVERLIMIT TRANSACTION"

    def test_expired_desc(self):
        assert REASON_DESCRIPTIONS[103] == "TRANSACTION RECEIVED AFTER ACCT EXPIRATION"
