from pathlib import Path

from app.db.connection import get_connection


SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)

    print("Database schema initialized successfully.")


if __name__ == "__main__":
    init_db()