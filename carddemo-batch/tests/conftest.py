import sys
from unittest.mock import MagicMock

pyspark_mock = MagicMock()
pyspark_sql_mock = MagicMock()
pyspark_sql_functions_mock = MagicMock()
pyspark_sql_types_mock = MagicMock()
pyspark_sql_window_mock = MagicMock()
delta_mock = MagicMock()

sys.modules["pyspark"] = pyspark_mock
sys.modules["pyspark.sql"] = pyspark_sql_mock
sys.modules["pyspark.sql.functions"] = pyspark_sql_functions_mock
sys.modules["pyspark.sql.types"] = pyspark_sql_types_mock
sys.modules["pyspark.sql.window"] = pyspark_sql_window_mock
sys.modules["delta"] = delta_mock
sys.modules["delta.tables"] = MagicMock()

pyspark_sql_mock.SparkSession = MagicMock()
pyspark_sql_mock.DataFrame = MagicMock()
pyspark_sql_mock.Window = MagicMock()
