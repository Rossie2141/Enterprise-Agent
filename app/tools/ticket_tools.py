from pathlib import Path

from langchain_core.tools import tool
from langgraph.types import interrupt

from app.db.connection import get_connection
from app.utils.errors import handle_tool_error


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "sample_data"
    / "tickets.csv"
)


@tool
def search_tickets(
    status: str = "",
    priority: str = "",
) -> list[dict]:
    """Search support tickets by status and/or priority.

    Args:
        status: Ticket status: open, pending, resolved, or unresolved.
        priority: Ticket priority: low, medium, or high.

    Returns:
        A list of matching tickets.
    """
    try:
        query = """
            SELECT
                ticket_id,
                customer_id,
                priority,
                status,
                subject,
                description,
                created_at
            FROM tickets
            WHERE 1=1
        """

        params = []

        if status:
            requested_status = status.strip().lower()

            if requested_status == "unresolved":
                query += " AND status IN (%s, %s)"
                params.extend(["open", "pending"])
            else:
                query += " AND status = %s"
                params.append(requested_status)

        if priority:
            query += " AND priority = %s"
            params.append(priority.strip().lower())

        query += " ORDER BY ticket_id"

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)

                rows = cur.fetchall()
                columns = [
                    description.name
                    for description in cur.description
                ]

                return [
                    dict(zip(columns, row))
                    for row in rows
                ]

    except Exception as e:
        return handle_tool_error(
            "search_tickets",
            e,
        )


@tool
def get_ticket(ticket_id: str) -> dict:
    """Retrieve a single support ticket by ticket ID.

    Args:
        ticket_id: The unique ticket ID, such as TCK-1005.

    Returns:
        The matching ticket or an error if not found.
    """
    try:
        query = """
            SELECT
                ticket_id,
                customer_id,
                priority,
                status,
                subject,
                description,
                created_at
            FROM tickets
            WHERE LOWER(ticket_id) = LOWER(%s)
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (ticket_id.strip(),),
                )

                row = cur.fetchone()

                if not row:
                    return {
                        "error": f"Ticket {ticket_id} not found."
                    }

                columns = [
                    description.name
                    for description in cur.description
                ]

                return dict(zip(columns, row))

    except Exception as e:
        return handle_tool_error(
            "get_ticket",
            e,
        )


@tool
def update_ticket(
    ticket_id: str,
    status: str = "",
    priority: str = "",
) -> dict:
    """Update the status and/or priority of a support ticket.

    Args:
        ticket_id: The unique ticket ID, such as TCK-1005.
        status: New status. Allowed values: open, pending, resolved.
        priority: New priority. Allowed values: low, medium, high.

    Returns:
        The updated ticket dictionary, or an error message.
    """

    valid_statuses = {
        "open",
        "pending",
        "resolved",
    }

    valid_priorities = {
        "low",
        "medium",
        "high",
    }

    requested_status = status.strip().lower()
    requested_priority = priority.strip().lower()
    requested_ticket_id = ticket_id.strip()

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if (
        requested_status
        and requested_status not in valid_statuses
    ):
        return {
            "error": (
                f"Invalid status '{status}'. "
                "Allowed values: open, pending, resolved."
            )
        }

    if (
        requested_priority
        and requested_priority not in valid_priorities
    ):
        return {
            "error": (
                f"Invalid priority '{priority}'. "
                "Allowed values: low, medium, high."
            )
        }

    try:
        # ----------------------------------------------------
        # Verify ticket exists BEFORE asking for approval
        # ----------------------------------------------------

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        ticket_id,
                        customer_id,
                        priority,
                        status,
                        subject,
                        description,
                        created_at
                    FROM tickets
                    WHERE LOWER(ticket_id) = LOWER(%s)
                    """,
                    (requested_ticket_id,),
                )

                existing_ticket = cur.fetchone()

                if not existing_ticket:
                    return {
                        "error": (
                            f"Ticket {ticket_id} not found."
                        )
                    }

                columns = [
                    description.name
                    for description in cur.description
                ]

                existing_ticket = dict(
                    zip(columns, existing_ticket)
                )

        # ----------------------------------------------------
        # Ask for human approval BEFORE modifying anything
        # ----------------------------------------------------

        approval = interrupt(
            {
                "action": "update_ticket",
                "ticket_id": ticket_id,
                "new_status": (
                    requested_status
                    or None
                ),
                "new_priority": (
                    requested_priority
                    or None
                ),
                "message": (
                    f"Approve updating ticket "
                    f"{ticket_id}?"
                ),
            }
        )

        # ----------------------------------------------------
        # Human rejected the operation
        # ----------------------------------------------------

        if not approval:
            return {
                "status": "cancelled",
                "message": (
                    f"Update to ticket "
                    f"{ticket_id} was cancelled."
                ),
            }

        # ----------------------------------------------------
        # Build dynamic UPDATE query
        # ----------------------------------------------------

        update_fields = []
        params = []

        if requested_status:
            update_fields.append(
                "status = %s"
            )
            params.append(
                requested_status
            )

        if requested_priority:
            update_fields.append(
                "priority = %s"
            )
            params.append(
                requested_priority
            )

        if not update_fields:
            return {
                "error": (
                    "No update fields were provided."
                )
            }

        params.append(requested_ticket_id)

        query = f"""
            UPDATE tickets
            SET {", ".join(update_fields)}
            WHERE LOWER(ticket_id) = LOWER(%s)
            RETURNING
                ticket_id,
                customer_id,
                priority,
                status,
                subject,
                description,
                created_at
        """

        # ----------------------------------------------------
        # Perform update
        # ----------------------------------------------------

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    params,
                )

                updated_row = cur.fetchone()

                columns = [
                    description.name
                    for description in cur.description
                ]

                if not updated_row:
                    return {
                        "error": (
                            f"Ticket {ticket_id} "
                            "could not be updated."
                        )
                    }

                return dict(
                    zip(columns, updated_row)
                )

    except Exception as e:
        return handle_tool_error(
            "update_ticket",
            e,
        )