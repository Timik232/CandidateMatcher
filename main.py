import json
import logging
import os
import time
from typing import Optional

import requests

from candidate import configure_logging, process_json, vacancies


def test_matcher(resume_path: Optional[str] = None):
    """
    Test function to check if the matcher works correctly.
    """

    url = "http://localhost:8000/candidate_match"
    if resume_path is None:
        resume_path = os.path.join("data", "Komolov.pdf")

    try:
        if not os.path.exists(resume_path):
            logging.error(f"Resume file not found: {resume_path}")
            return
        with open(resume_path, "rb") as f:
            files = {
                "files": (
                    os.path.basename(resume_path),
                    f,
                    "application/octet-stream",
                )
            }
            resp = requests.post(url, files=files)

        logging.info("Status: %s", resp.status_code)
        logging.info("Response JSON: %s", resp.json())

    except Exception as e:
        logging.error(f"Error in test_matcher: {str(e)}")


def main(test_path: str):
    with open(test_path, "r", encoding="utf-8") as file:
        test_data = json.load(file)
    result = process_json(test_data, vacancies)
    logging.info(result)


if __name__ == "__main__":
    start = time.time()
    configure_logging(logging.DEBUG)
    test_path = os.path.join("data", "example.json")
    test_matcher()
    main(test_path)
    end = time.time()
    print("Time elapsed: %f" % (end - start))
