from app.services.report_service import submit_report


class TestSubmitReport:
    def test_returns_job_id(self):
        result = submit_report({
            "report_type": "transaction",
            "start_year": 2025,
            "start_month": 1,
            "end_year": 2025,
            "end_month": 6,
        })
        assert result["job_id"].startswith("RPT-")
        assert result["report_type"] == "transaction"
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-06-01"

    def test_single_digit_month_padded(self):
        result = submit_report({
            "report_type": "balance",
            "start_year": 2025,
            "start_month": 3,
            "end_year": 2025,
            "end_month": 9,
        })
        assert result["start_date"] == "2025-03-01"
        assert result["end_date"] == "2025-09-01"

    def test_message_contains_report_type(self):
        result = submit_report({
            "report_type": "statement",
            "start_year": 2025,
            "start_month": 1,
            "end_year": 2025,
            "end_month": 12,
        })
        assert "statement" in result["message"]
