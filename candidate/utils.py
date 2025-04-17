import json
import logging
import os
from typing import Iterator

import ollama
from ollama import ChatResponse
from pydantic import BaseModel, Field

SYSTEM_PROMPT = (
    "Ты – HR-менеджер, который отбирает людей на должность. По представленным навыкам тебе необходимо"
    "оценить, подходит ли кандидат на должность, и если подходит, то на какую."
)

VACANCIES_PATH = os.path.join("data", "vacancies.json")
if os.path.exists(VACANCIES_PATH):
    with open(VACANCIES_PATH, "r", encoding="utf-8") as file:
        vacancies = json.load(file)
else:
    vacancies = {}

API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
MODEL_NAME = os.environ.get("OLLAMA_MODEL_NAME", "gemma3:4b")
ollama.base_url = API_URL


class VacancySchema(BaseModel):
    """
    Pydantic model generated from JSON Schema draft-07:
    title: VacancySchema
    """

    vacancy: str = Field(..., description="Название вакансии, на которую подходит")
    explaining: str = Field(..., description="Описание")


def ollama_chat(
    client: ollama.Client,
    model_name: str,
    prompt: str,
    system: str | None = None,
    schema: dict | None = None,
    stream: bool = False,
) -> str | Iterator[ChatResponse]:
    """
    Wrapper function to send a chat-style request to Ollama, optionally with a system prompt
    and JSON-schema formatting.

    Args:
        client (ollama.Client): The Ollama client instance.
        model_name (str): The name of the model in Ollama.
        prompt (str): The user's message content.
        system (str | None): Optional system‑level instruction to guide the model.
        schema (dict | None): Optional JSON schema for structured output.
        stream (bool): Whether to return an iterator that yields streaming responses.

    Returns:
        str: The model's reply content (or JSON string if schema is provided).
    """
    params: dict = {
        "model": model_name,
        "messages": [],
        "stream": stream,
    }

    if system is not None:
        params["messages"].append({"role": "system", "content": system})
    params["messages"].append({"role": "user", "content": prompt})

    if schema is not None:
        params["format"] = schema

    try:
        response = client.chat(**params)
        logging.debug(f"response: {response}")

        if not stream:
            return response["message"]["content"]

        return response
    except Exception as e:
        logging.error(f"Error calling Ollama API: {e}")
        raise
