from app.models.llm import get_llm


def main():
    llm = get_llm()

    response = llm.invoke(
        "Explain what an enterprise AI agent is in one sentence."
    )

    print("\nResponse:")
    print(response.content)


if __name__ == "__main__":
    main()