import os

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI

from models.config import LLMManager


def test_model_call():
    _ = load_dotenv(find_dotenv())
    model_name = os.getenv("MODEL")
    LLMManager.use_llm("deepseek")
    llm: ChatOpenAI = LLMManager.get_llm_client()
    response = llm.invoke("hello")
    print("test_model_call called", model_name, response)
