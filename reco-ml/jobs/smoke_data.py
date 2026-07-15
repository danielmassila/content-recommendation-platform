from reco_ml.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        print("connected OK:", cur.fetchone())
