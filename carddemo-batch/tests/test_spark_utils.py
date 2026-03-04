import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.spark_utils import get_db_prefix


class TestGetDbPrefix:
    def test_without_catalog(self):
        result = get_db_prefix("", "carddemo")
        assert result == "carddemo"

    def test_with_catalog(self):
        result = get_db_prefix("my_catalog", "carddemo")
        assert result == "carddemo"

    def test_custom_database(self):
        result = get_db_prefix("", "mydb")
        assert result == "mydb"
