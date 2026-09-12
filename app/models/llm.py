from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import os

load_dotenv()


def get_llm():

    hf_token = os.getenv("HF_TOKEN")

    if not hf_token:
        raise ValueError("HF_TOKEN is not set in the .env file.")

    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-72B-Instruct",
        huggingfacehub_api_token=hf_token,
        temperature=0.1,
        max_new_tokens=512,
    )

    return ChatHuggingFace(llm=llm)