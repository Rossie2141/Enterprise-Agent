import psycopg


def get_connection():
    return psycopg.connect(
        host="localhost",
        port=5433,
        dbname="enterprise_agent",
        user="agent_user",
        password="agent_password",
    )