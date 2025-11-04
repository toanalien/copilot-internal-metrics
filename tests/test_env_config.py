import os
import re

from dotenv import load_dotenv


def test_database_url_from_env_present_and_format():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    assert url, "DATABASE_URL not found in environment/.env"
    assert re.match(r"^postgresql://.+:.+@postgres:5432/.+$", url), "DATABASE_URL must point to postgres service"