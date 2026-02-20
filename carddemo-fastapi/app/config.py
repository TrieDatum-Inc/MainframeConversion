import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://carddemo:carddemo12345@localhost:3306/carddemo"
)

SECRET_KEY = os.getenv("SECRET_KEY", "carddemo-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
