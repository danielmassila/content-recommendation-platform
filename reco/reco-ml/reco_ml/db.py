from reco_ml.config import db_dsn
import psycopg
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Establish and return a connection to the PostgreSQL database."""
    conn = psycopg.connect(db_dsn())
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    else:
        conn.commit()
    finally:
        conn.close()
