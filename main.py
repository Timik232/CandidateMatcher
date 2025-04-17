import json
import logging
import os
from typing import Optional

import requests

from candidate import configure_logging, process_json, vacancies


def test_matcher(extracted_json_path: Optional[str] = None):
    """
    Test function to check if the matcher works correctly.
    """
    if extracted_json_path is None:
        extracted_json_path = os.path.join("data", "example.json")
    with open(extracted_json_path, "r", encoding="utf-8") as file:
        test_data = json.load(file)
    url = "http://localhost:8000/candidate_match"
    response = requests.post(url, json=test_data)
    logging.info(response)


def main(test_path: str):
    with open(test_path, "r", encoding="utf-8") as file:
        test_data = json.load(file)
    result = process_json(test_data, vacancies)
    print(result)


if __name__ == "__main__":
    configure_logging(logging.DEBUG)
    test_path = os.path.join("data", "example.json")
    # test_matcher()
    main(test_path)
