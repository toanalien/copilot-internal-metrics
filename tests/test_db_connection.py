from app.db import check_db_connection, init_db


def test_db_connects_and_tables_exist():
    # Ensure tables are created and a simple query works
    init_db()
    assert check_db_connection() is True