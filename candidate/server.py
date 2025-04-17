from fastapi import FastAPI, HTTPException, Request

from . import process_json, vacancies

app = FastAPI()


@app.post("/candidate_match")
async def process_candidate(request: Request):
    try:
        data = await request.json()

        result = process_json(data, vacancies)

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки JSON: {str(e)}")


@app.get("/")
async def root():
    return {"message": "Candidate Match API is working"}
