import csv
from pathlib import Path

from app.db.connection import get_connection


CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "sample_data"
    / "tickets.csv"
)


def seed_tickets():
    with open(CSV_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        tickets = list(reader)

    with get_connection() as conn:
        with conn.cursor() as cur:
            for ticket in tickets:
                cur.execute(
                    """
                    INSERT INTO tickets (
                        ticket_id,
                        customer_id,
                        priority,
                        status,
                        subject,
                        description,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticket_id)
                    DO UPDATE SET
                        customer_id = EXCLUDED.customer_id,
                        priority = EXCLUDED.priority,
                        status = EXCLUDED.status,
                        subject = EXCLUDED.subject,
                        description = EXCLUDED.description,
                        created_at = EXCLUDED.created_at;
                    """,
                    (
                        ticket["ticket_id"],
                        ticket["customer_id"],
                        ticket["priority"],
                        ticket["status"],
                        ticket["subject"],
                        ticket["description"],
                        ticket["created_at"],
                    ),
                )

    print(f"Seeded {len(tickets)} tickets successfully.")


if __name__ == "__main__":
    seed_tickets()