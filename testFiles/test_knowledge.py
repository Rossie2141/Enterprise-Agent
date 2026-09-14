from app.tools.knowledge_tools import search_knowledge


def main():
    queries = [
        "How long do customers have to request a refund?",
        "What should I do if a customer cannot log in?",
        "What happens when the production API is failing?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")

        results = search_knowledge.invoke({
            "query": query,
            "limit": 2,
        })

        for result in results:
            print(
                f"\nTitle: {result['title']}"
                f"\nSimilarity: {result['similarity']:.4f}"
                f"\n{result['content']}"
            )


if __name__ == "__main__":
    main()