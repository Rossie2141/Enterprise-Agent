from app.tools.ticket_tools import search_tickets, get_ticket


def main():
    print("\n=== Search high-priority tickets ===")

    results = search_tickets.invoke({
        "priority": "high"
    })

    for ticket in results:
        print(ticket["ticket_id"], ticket["status"])


    print("\n=== Get TCK-1005 ===")

    ticket = get_ticket.invoke({
        "ticket_id": "TCK-1005"
    })

    print(ticket)


if __name__ == "__main__":
    main()