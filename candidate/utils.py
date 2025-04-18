""" Файл для вспомогательных функций и констант """
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
    Pydantic-схема для структурированного ответа от модели Ollama.:
    title: VacancySchema
    """

    vacancy: str = Field(..., description="Название вакансии")
    percentage: int = Field(
        ..., description="Процент соответствия кандидата вакансии от 0 до 100"
    )
    explaining: str = Field(..., description="Описание соответствия кандидата вакансии")
    recommendations: str = Field(..., description="Рекомендации по улучшению навыков")


def ollama_chat(
    client: ollama.Client,
    model_name: str,
    prompt: str,
    system: str | None = None,
    schema: dict | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.4,
    stream: bool = False,
) -> str | Iterator[ChatResponse]:
    """
    Функция-оболочка для отправки Ollama запроса в виде чата, с системным промптом
    и форматированием в формате JSON-схемы.

    Args:
        client (ollama.Client): Клиент ollama.
        model_name (str): название модели в Ollama.
        prompt (str): Основный промпт.
        system (str | None): Системный промпт
        schema (dict | None): Опциональная Json-схема для форматирования ответа.
        max_tokens (int): Максимальное количество токенов
        temperature (float): Температура для генерации текста.
        stream (bool): Следует ли возвращать итератор, который выдает потоковые ответы.

    Returns:
        str: Содержимое ответа модели (или строка JSON, если указана схема).
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
        response = client.chat(
            **params,
            options={
                "num_ctx": max_tokens,
                "temperature": temperature,
            },
        )
        logging.debug(f"response: {response}")

        if not stream:
            return response["message"]["content"]

        return response
    except Exception as e:
        logging.error(f"Error calling Ollama API: {e}")
        raise
