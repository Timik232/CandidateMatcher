import json
import os

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

API_URL = "http://localhost:1234/v1"
MODEL_NAME = "gemma-3-4b-it"
