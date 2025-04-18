import os
import tempfile
from contextlib import suppress
from typing import Annotated, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile

from .llm_match import process_json
from .module_nlp import extract_brief
from .utils import vacancies

app = FastAPI()


@app.post("/candidate_match")
async def process_candidate(files: Annotated[UploadFile, File(...)]) -> Dict:
    """
    Принимает файл резюме в формате multipart/form-data,
    сохраняет его во временную директорию, передает путь в extract_brief,
    обрабатывает результат через process_json и возвращает его.
    """
    # 1) Сохраняем файл во временную папку
    try:
        suffix = os.path.splitext(files.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            content = await files.read()
            tmp.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Не удалось сохранить файл: {e}"
        ) from e

    # 2) Извлекаем данные из резюме
    try:
        resume_dict = extract_brief(temp_path)
    except Exception as e:
        # удаляем временный файл перед поднятием ошибки
        os.unlink(temp_path)
        raise HTTPException(
            status_code=400, detail=f"Ошибка при обработке резюме: {e}"
        ) from e

    # 3) Удаляем временный файл
    with suppress(OSError):
        os.unlink(temp_path)

    # 4) Совмещаем с вакансией и возвращаем результат
    try:
        result = process_json(resume_dict, vacancies)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка при обработке данных: {e}"
        ) from e


@app.get("/")
async def root():
    return {"message": "Candidate Match API is working"}
