from app.db.connection import get_connection


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()

    print("PostgreSQL connection successful!")
    print(version[0])


if __name__ == "__main__":
    main()