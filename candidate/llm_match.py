"""Файл с логикой соотношения вакансий и кандидатов."""
import json
import logging
from typing import Dict

import ollama

from .utils import API_URL, MODEL_NAME, SYSTEM_PROMPT, VacancySchema, ollama_chat

client = ollama.Client(host=API_URL)


def validate_input_data(data: Dict, vacancies: Dict) -> tuple:
    """
    Валидирует формат входных данных кандидата и вакансий.

    Args:
        data: Данные кандидата
        vacancies: Словарь вакансий

    Returns:
        tuple: (bool, str) - Результат проверки и сообщение об ошибке
    """
    try:
        # Валидация данных кандидата
        if not isinstance(data, dict):
            return False, "Candidate data must be a dictionary"

        if not all(key in data for key in ["skills", "experience"]):
            return False, "Missing required fields in candidate data"

        if not isinstance(data["skills"], list) or not isinstance(
            data["experience"], list
        ):
            return False, "Skills and experience must be lists"

        # Валидация данных вакансий
        if not isinstance(vacancies, dict) or len(vacancies) == 0:
            return False, "Vacancies must be a non-empty dictionary"

        for vac_id, vacancy in vacancies.items():
            if not isinstance(vacancy, dict):
                return False, f"Vacancy {vac_id} must be a dictionary"

            if "название" not in vacancy or "компетенции" not in vacancy:
                return (
                    False,
                    f"Vacancy {vac_id} missing required fields ('название' или 'компетенции')",
                )

        return True, ""

    except Exception as e:
        return False, f"Validation error: {str(e)}"


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
                "vacancy": "Название лучшей вакансии",
                "percentage": int,
                "explaining": "Текст оценки",
                "recommendations": [список рекомендаций]
            }
            или {"error": ...} в случае ошибки

    Examples:
        >>> candidate_data = {"skills": ["Python"], "experience": ["Разработка"]}
        >>> job_vacancies = {"1": {"название": "Программист", "компетенции": {...}}}
        >>> process_json(candidate_data, job_vacancies)
        {
            "vacancy": "Программист",
            "percentage": 85,
            "explaining": "Соответствует основным требованиям...",
            "recommendations": "Следует изучить..."
        }

    Notes:
        - Использует глобальный клиент LLM для генерации оценок
        - Логика расчета процента соответствия:
            * -2% за навык уровня "низкий"
            * -5% за навык уровня "средний"
            * -10% за навык уровня "высокий"
        - Парсинг ответа проводится согласно VacancySchema
        - В случае ошибки декодирования JSON возвращает словарь с ошибкой
    """
    global client
    is_valid, error_msg = validate_input_data(data, vacancies)
    if not is_valid:
        logging.error(f"Input validation failed: {error_msg}")
        return {"error": f"Invalid input data: {error_msg}"}
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
            "Используй следующую логику вычитания процентов: \n"
            + "- 2 процента за каждый отсутствующий навык уровня 'низкий'\n"
            + "- 5 процентов за каждый отсутствующий навык уровня 'средний'\n"
            + "- 10 процентов за каждый отсутствующий навык уровня 'высокий'\n"
            + "- Если среди компетенций есть обширная сфера, а у кандидата есть более узкие навыки из этой сферы, "
            "то вычитать не нужно. В "
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
            try:
                vacancy_name = vacancies[vacancy]["название"]
                fallback_response = {
                    "vacancy": vacancy_name,
                    "percentage": 0,
                    "explaining": f"Не удалось обработать ответ для вакансии {vacancy_name}.",
                    "recommendations": "Попробуйте повторить запрос или скорректировать данные.",
                }
                answers.append(fallback_response)
                logging.warning(f"Created fallback response for {vacancy_name}")
            except Exception as e:
                logging.error(f"Failed to create fallback response: {str(e)}")

    if not answers:
        return {"error": "No answers from LLM"}

    best = max(answers, key=lambda x: x["percentage"])

    best["full_name"] = data["base_info"]["full_name"].split("\n")[0]
    best["email"] = data["contacts"]["email"]
    best["phone"] = data["contacts"]["phone"]
    return best
