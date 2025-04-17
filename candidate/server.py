from typing import Dict

from fastapi import FastAPI, HTTPException, UploadFile

from .llm_match import process_json
from .utils import vacancies

app = FastAPI()


@app.post("/candidate_match")
async def process_candidate(request: UploadFile) -> Dict:
    try:
        data = await request.read()

        result = process_json(data, vacancies)

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки JSON: {str(e)}")


@app.get("/")
async def root():
    return {"message": "Candidate Match API is working"}
