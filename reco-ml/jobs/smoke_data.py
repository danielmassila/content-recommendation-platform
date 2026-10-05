"""Check PostgreSQL connectivity without reading application data."""

from reco_ml.db import get_db_connection


def main():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            print("connected OK:", cursor.fetchone())


if __name__ == '__main__':
    main()
