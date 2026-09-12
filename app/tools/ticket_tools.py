import csv
from pathlib import Path

from langchain_core.tools import tool
from langgraph.types import interrupt


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_data" / "tickets.csv"


@tool
def search_tickets(
    status: str = "",
    priority: str = "",
) -> list[dict]:
    """Search support tickets by status and/or priority.

    Args:
        status: The ticket status to filter by. Valid options are 'open', 'pending',
            'resolved', or 'unresolved' (which matches all open and pending tickets).
            Leave empty to match all statuses.
        priority: The ticket priority to filter by. Valid options are 'low',
            'medium', or 'high'. Leave empty to match all priorities.

    Returns:
        A list of matching ticket dictionaries.
    """

    results = []

    with open(DATA_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for ticket in reader:
            ticket_status = ticket.get("status", "").strip().lower()
            ticket_priority = ticket.get("priority", "").strip().lower()

            if status:
                req_status = status.strip().lower()
                if req_status == "unresolved":
                    if ticket_status == "resolved":
                        continue
                elif ticket_status != req_status:
                    continue

            if priority:
                req_priority = priority.strip().lower()
                if ticket_priority != req_priority:
                    continue

            results.append(ticket)

    return results

@tool
def get_ticket(ticket_id: str) -> dict:
    """Retrieve a single support ticket by ticket ID.

    Args:
        ticket_id: The unique ticket ID, such as 'TCK-1005'.

    Returns:
        The matching ticket dictionary, or an error if not found.
    """

    with open(DATA_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for ticket in reader:
            if ticket.get("ticket_id", "").strip().lower() == ticket_id.strip().lower():
                return ticket

    return {
        "error": f"Ticket {ticket_id} not found."
    }

@tool
def update_ticket(
    ticket_id: str,
    status: str = "",
    priority: str = "",
) -> dict:
    """Update the status and/or priority of a support ticket.

    Args:
        ticket_id: The unique ticket ID, such as 'TCK-1005'.
        status: New status. Allowed values: open, pending, resolved.
        priority: New priority. Allowed values: low, medium, high.

    Returns:
        The updated ticket dictionary, or an error message.
    """

    valid_statuses = {"open", "pending", "resolved"}
    valid_priorities = {"low", "medium", "high"}

    requested_status = status.strip().lower()
    requested_priority = priority.strip().lower()
    requested_ticket_id = ticket_id.strip().lower()

    # Validate status
    if requested_status and requested_status not in valid_statuses:
        return {
            "error": (
                f"Invalid status '{status}'. "
                "Allowed values: open, pending, resolved."
            )
        }

    # Validate priority
    if requested_priority and requested_priority not in valid_priorities:
        return {
            "error": (
                f"Invalid priority '{priority}'. "
                "Allowed values: low, medium, high."
            )
        }

    # Ask for human approval BEFORE modifying anything
    approval = interrupt(
        {
            "action": "update_ticket",
            "ticket_id": ticket_id,
            "new_status": requested_status or None,
            "new_priority": requested_priority or None,
            "message": (
                f"Approve updating ticket {ticket_id}?"
            ),
        }
    )

    # Human rejected the operation
    if not approval:
        return {
            "status": "cancelled",
            "message": f"Update to ticket {ticket_id} was cancelled."
        }

    # Read all tickets
    with open(DATA_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        tickets = list(reader)

    # Find and update ticket
    ticket_found = False
    updated_ticket = None

    for ticket in tickets:
        if ticket.get("ticket_id", "").strip().lower() == requested_ticket_id:
            ticket_found = True

            if requested_status:
                ticket["status"] = requested_status

            if requested_priority:
                ticket["priority"] = requested_priority

            updated_ticket = ticket
            break

    if not ticket_found:
        return {
            "error": f"Ticket {ticket_id} not found."
        }

    # Write updated data back to CSV
    fieldnames = [
        "ticket_id",
        "customer_id",
        "priority",
        "status",
        "subject",
        "description",
        "created_at",
    ]

    with open(DATA_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(tickets)

    return updated_ticket