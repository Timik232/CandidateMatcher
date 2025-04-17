import json
import logging
from typing import Dict

import openai

from . import API_URL, MODEL_NAME, SYSTEM_PROMPT

client = openai.OpenAI(base_url=API_URL, api_key="<KEY>")


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
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model=MODEL_NAME,
        )
        answers.append(response.choices[0].message.content)
    prompt = "Твои предыдущие оценки по вакансиям: " + "\n"
    prompt += "\n".join(answers) + "\n"

    prompt += (
        "Теперь напиши, на какую вакансию лучше всего подходит кандидат из всех, и почему именно на нее."
        "Если он не подходит ни по одной, то напиши об этом и скажи, что кандидату нужно изучить"
    )
    logging.debug(prompt)
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model=MODEL_NAME,
    )
    try:
        response = json.loads(response.choices[0].message.content)
    except json.decoder.JSONDecodeError:
        response = {"error": "Invalid JSON response"}
    return response
