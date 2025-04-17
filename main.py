import json
import logging
import os

from candidate import configure_logging, process_json, vacancies


def main(test_path: str):
    configure_logging(logging.DEBUG)
    with open(test_path, "r", encoding="utf-8") as file:
        test_data = json.load(file)
    result = process_json(test_data, vacancies)
    print(result)


if __name__ == "__main__":
    test_path = os.path.join("data", "example.json")
    main(test_path)
