from app.agents.router import route_request


def main():
    test_requests = [
        "Show me all high priority tickets.",
        "What is the refund policy?",
        "What is the refund policy and which high priority tickets are open?",
        "Hello, how are you?",
    ]

    for request in test_requests:
        route = route_request(request)

        print(f"\nRequest: {request}")
        print(f"Route:   {route}")


if __name__ == "__main__":
    main()