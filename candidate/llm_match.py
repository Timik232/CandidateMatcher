import json
import logging
from typing import Dict

import ollama

from .utils import MODEL_NAME, SYSTEM_PROMPT, VacancySchema, ollama_chat

client = ollama.Client()


def process_json(data: Dict, vacancies: Dict) -> Dict:
    """
    Process the input JSON data and return a response.
    :param vacancies: vacancies from the company
    :param data: dict from the json
    :return: str
    """
    global client
    correspond_dict = {
        1: "низкий",
        2: "средний",
        3: "высокий",
    }
    answers = []
    for vacancy in vacancies:
        prompt = "Вакансия: " + vacancies[vacancy]["название"] + "\n"
        # prompt += "Описание: " + vacancies[vacancy]["описание"] + "\n"
        prompt += "Компетенции, необходимые для выполнения работы: " + "\n"
        for skill in vacancies[vacancy]["компетенции"]:
            for number in range(len(vacancies[vacancy]["компетенции"][skill])):
                prompt += (
                    vacancies[vacancy]["компетенции"][skill][number]["название"]
                    + ", уровень: "
                    + correspond_dict[
                        (vacancies[vacancy]["компетенции"][skill][number]["уровень"])
                    ]
                    + "\n"
                )
        prompt += "\n"
        prompt += (
            "Тебе необходимо оценить, насколько подходит кандидат на должность, и если не подходит,"
            "то написать рекомендации по обучению. В начале ответа пиши название вакансии, затем подходит"
            "или нет, и в конце рекомендации по обучению, если кандидат не подходит.\n"
            "Его навыки: " + "\n"
        )
        prompt += ", ".join(data["skills"]) + "\n"
        prompt += "Также его опыт включал: " + "\n"
        prompt += ", ".join(data["experience"]) + "\n"
        prompt += "Твоя оценка: "
        logging.debug(prompt)
        response = ollama_chat(
            client, model_name=MODEL_NAME, prompt=prompt, system=SYSTEM_PROMPT
        )
        answers.append(response)
    prompt = "Твои предыдущие оценки по вакансиям: " + "\n"
    prompt += "\n".join(answers) + "\n"

    prompt += (
        "Теперь напиши, на какую вакансию лучше всего подходит кандидат из всех, и почему именно на нее."
        "Если он не подходит ни по одной, то напиши об этом и скажи, что кандидату нужно изучить"
    )
    logging.debug(prompt)
    response = ollama_chat(
        client,
        model_name=MODEL_NAME,
        prompt=prompt,
        system=SYSTEM_PROMPT,
        schema=VacancySchema.model_json_schema()(),
    )
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        response = {"error": "Invalid JSON response"}
    return response
