import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    """
    Create a PostgreSQL database connection.

    Database configuration is loaded from environment variables,
    with local development defaults as fallback.
    """

    try:
        return psycopg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5433"),
            dbname=os.getenv(
                "DB_NAME",
                "enterprise_agent",
            ),
            user=os.getenv(
                "DB_USER",
                "agent_user",
            ),
            password=os.getenv(
                "DB_PASSWORD",
                "agent_password",
            ),
            connect_timeout=5,
        )

    except psycopg.Error as e:
        raise RuntimeError(
            "Unable to connect to the PostgreSQL database."
        ) from e