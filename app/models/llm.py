import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


def get_llm():
    """
    Create and return the Groq chat model.
    """

    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is not set in the .env file."
        )

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.1,
        max_tokens=512,
        api_key=groq_api_key,
        max_retries=2,
    )

    return llm