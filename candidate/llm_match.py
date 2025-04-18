"""Файл с логикой соотношения вакансий и кандидатов."""
import json
import logging
from typing import Dict

import ollama

from .utils import MODEL_NAME, SYSTEM_PROMPT, VacancySchema, ollama_chat

client = ollama.Client()


def process_json(data: Dict, vacancies: Dict) -> Dict:
    """
    Обрабатывает данные кандидата и вакансии, возвращая рекомендации по трудоустройству.

    Функция выполняет комплексный анализ соответствия кандидата вакансиям:
    1. Генерирует промпты для оценки по каждой вакансии
    2. Рассчитывает процент соответствия на основе недостающих компетенций
    3. Формирует финальные рекомендации по наиболее подходящей вакансии

    Args:
        data (Dict): Данные кандидата в формате:
            {
                "skills": [список навыков],
                "experience": [список элементов опыта]
            }
        vacancies (Dict): Словарь вакансий в формате:
            {
                "vacancy_id": {
                    "название": "Название вакансии",
                    "компетенции": {
                        "категория": [
                            {
                                "название": "Название навыка",
                                "уровень": 1-3
                            }
                        ]
                    }
                }
            }

    Returns:
        Dict: Результат анализа в формате:
            {
                "вакансия": "Название лучшей вакансии",
                "процент_соответствия": int,
                "обоснование": "Текст оценки",
                "рекомендации": [список рекомендаций]
            }
            или {"error": ...} в случае ошибки

    Examples:
        >>> candidate_data = {"skills": ["Python"], "experience": ["Разработка"]}
        >>> job_vacancies = {"1": {"название": "Программист", "компетенции": {...}}}
        >>> process_json(candidate_data, job_vacancies)
        {
            "vacancy": "Программист",
            "percentage": 85,
            "explaining": "Соответствует основным требованиям..."
        }

    Notes:
        - Использует глобальный клиент LLM для генерации оценок
        - Логика расчета процента соответствия:
            * -2% за навык уровня "низкий"
            * -5% за навык уровня "средний"
            * -10% за навык уровня "высокий"
            * Не учитывает узкие навыки в рамках широкой категории
        - Парсинг ответа проводится согласно VacancySchema
        - В случае ошибки декодирования JSON возвращает словарь с ошибкой
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
            "или нет, и в конце рекомендации по обучению, если кандидат не подходит. Также укажи"
            "процент соответствия вакансии, в json-формате. "
            "Вычитай по 2 процента за навык уровня 'низкий', по 5 за средний"
            "и 10 за уровень высокий. Если среди компетенций есть обширная сфера, а"
            "у кандидата есть более узкие навыки из этой обширной сферы, то вычитать не нужно. В"
            "обосновании нужно писать, каких навыков не хватает, но не нужно указывать, что ты"
            "вычитаешь. \n"
            "Его навыки: " + "\n"
        )
        prompt += ", ".join(data["skills"]) + "\n"
        prompt += "Также его опыт включал: " + "\n"
        prompt += ", ".join(data["experience"]) + "\n"
        prompt += "Твоя оценка: "
        logging.debug(prompt)
        response = ollama_chat(
            client,
            model_name=MODEL_NAME,
            prompt=prompt,
            system=SYSTEM_PROMPT,
            schema=VacancySchema.model_json_schema(),
        )
        logging.debug("_____________________")
        logging.debug(response)
        try:
            answers.append(json.loads(response))
        except json.decoder.JSONDecodeError:
            logging.error("Invalid JSON response after LLM generation")

    if not answers:
        return {"error": "No answers from LLM"}

    best = max(answers, key=lambda x: x["percentage"])

    return best
