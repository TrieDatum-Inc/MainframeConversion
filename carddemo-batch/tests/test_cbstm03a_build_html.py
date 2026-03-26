import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jobs.cbstm03a_account_statement import _build_html_statement


class TestBuildHtmlStatement:
    def test_basic_output(self):
        html = _build_html_statement(
            cust_first="John",
            cust_last="Doe",
            addr_line1="123 Main St",
            addr_line2="",
            addr_line3="",
            state="CA",
            zipcode="90210",
            acct_id=10000000001,
            card_num="4111111111111111",
            stmt_date="2025-01-01",
            curr_bal=500.0,
            credit_limit=5000.0,
            transactions=[],
        )
        assert "<!DOCTYPE html>" in html
        assert "John Doe" in html
        assert "123 Main St" in html
        assert "10000000001" in html
        assert "4111111111111111" in html
        assert "500.00" in html
        assert "5,000.00" in html
        assert "4,500.00" in html

    def test_with_transactions(self):
        txns = [
            {
                "tran_date": "2025-01-15",
                "tran_id": "T001",
                "tran_type_cd": "01",
                "tran_cat_cd": 1,
                "tran_source": "POS",
                "tran_desc": "Store Purchase",
                "tran_amt": 150.00,
            },
            {
                "tran_date": "2025-01-20",
                "tran_id": "T002",
                "tran_type_cd": "02",
                "tran_cat_cd": 2,
                "tran_source": "ONLINE",
                "tran_desc": "Return",
                "tran_amt": -50.00,
            },
        ]
        html = _build_html_statement(
            cust_first="Jane",
            cust_last="Smith",
            addr_line1="456 Oak Ave",
            addr_line2="Suite 100",
            addr_line3="",
            state="NY",
            zipcode="10001",
            acct_id=20000000001,
            card_num="5222222222222222",
            stmt_date="2025-02-01",
            curr_bal=1000.0,
            credit_limit=10000.0,
            transactions=txns,
        )
        assert "Jane Smith" in html
        assert "Suite 100" in html
        assert "T001" in html
        assert "T002" in html
        assert "Store Purchase" in html
        assert "Return" in html
        assert "150.00" in html
        assert "-50.00" in html

    def test_addr_line3_included(self):
        html = _build_html_statement(
            cust_first="Bob",
            cust_last="Jones",
            addr_line1="789 Elm",
            addr_line2="Apt 2",
            addr_line3="Building C",
            state="TX",
            zipcode="75001",
            acct_id=30000000001,
            card_num="6333333333333333",
            stmt_date="2025-03-01",
            curr_bal=0.0,
            credit_limit=3000.0,
            transactions=[],
        )
        assert "Building C" in html

    def test_available_credit_calculation(self):
        html = _build_html_statement(
            cust_first="Test",
            cust_last="User",
            addr_line1="Test St",
            addr_line2="",
            addr_line3="",
            state="FL",
            zipcode="33101",
            acct_id=40000000001,
            card_num="7444444444444444",
            stmt_date="2025-04-01",
            curr_bal=2000.0,
            credit_limit=5000.0,
            transactions=[],
        )
        assert "3,000.00" in html

    def test_html_escaping(self):
        html = _build_html_statement(
            cust_first="<script>",
            cust_last="alert('xss')",
            addr_line1="<b>bold</b>",
            addr_line2="",
            addr_line3="",
            state="CA",
            zipcode="90210",
            acct_id=50000000001,
            card_num="8555555555555555",
            stmt_date="2025-05-01",
            curr_bal=0.0,
            credit_limit=1000.0,
            transactions=[],
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "<b>bold</b>" not in html
