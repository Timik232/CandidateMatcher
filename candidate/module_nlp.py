# Файл для извлечения информации из резюме
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import docx
import pdfplumber
import spacy
import yake
from rapidfuzz import fuzz, process

nlp = spacy.load("ru_core_news_md")

HEADER_MAP = {
    "skills": ["навыки", "skills", "технические навыки", "компетенции", "tech stack"],
    "experience": ["опыт", "опыт работы", "projects", "проект", "work experience"],
    "education": ["образование", "учеба", "education"],
    "contacts": ["контакты", "contact", "связь"],
    "about": ["обо мне", "о себе", "about me", "about"],
    "languages": ["языки", "languages"],
    "achievements": ["достижения", "achievements", "awards"],
    "projects": ["проект", "проекты", "проектов", "project", "projects"],
}


def extract_text_from_pdf(file_path: str) -> str:
    """Извлекает текст из PDF-файла.

    Args:
        file_path: Путь к PDF-файлу

    Returns:
        str: Текст, извлеченный из всех страниц PDF
    """
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    pdf.close()
    return text


def extract_text_from_docx(file_path: str) -> str:
    """Извлекает текст из документа DOCX.

    Args:
        file_path: Путь к DOCX-файлу

    Returns:
        str: Текст, извлеченный из всех параграфов документа
    """
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


def extract_text(file_path: str) -> str:
    """Извлекает текст из файла в зависимости от его формата.

    Args:
        file_path: Путь к файлу (поддерживаются .pdf, .docx и .txt)

    Returns:
        str: Извлеченный текст

    Raises:
        ValueError: Если формат файла не поддерживается
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_contacts(text: str) -> Dict[str, str]:
    """Извлекает контактные данные из текста резюме.

    Args:
        text: Текст резюме

    Returns:
        Dict[str, str]: Словарь с найденными контактами (email, телефон, соцсети)
    """
    contacts = {}

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        contacts["email"] = email_match.group(0)

    phone_match = re.search(
        r"(?:(?:8|\+7)[\- ]?)?(?:\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}", text
    )
    if phone_match:
        contacts["phone"] = phone_match.group(0)

    telegram_match = re.search(r"@[\w\d_]+", text)
    if telegram_match:
        tag = telegram_match.group(0)
        if not re.match(r"[\w\.-]+@[\w\.-]+\.\w+", tag):
            contacts["telegram"] = tag

    github_match = re.search(r"(https?://)?(www\.)?github\.com/[^\s\n]+", text)
    if github_match:
        contacts["github"] = github_match.group(0)

    vk_match = re.search(
        r"(https?://)?(www\.)?(vk\.com/[^\s\n]+|вконтакте|вк|vk@[\w\d_]+)",
        text,
        re.IGNORECASE,
    )
    if vk_match:
        contacts["vk"] = vk_match.group(0)

    hh_match = re.search(r"(https?://)?(www\.)?hh\.ru/[^\s\n]+", text)
    if hh_match:
        contacts["hh"] = hh_match.group(0)

    linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/[^\s\n]+", text)
    if linkedin_match:
        contacts["linkedin"] = linkedin_match.group(0)

    return contacts


def normalize_header(line: str) -> Optional[str]:
    """Определяет категорию заголовка по нечеткому соответствию.

    Args:
        line: Текст заголовка для анализа

    Returns:
        Optional[str]: Нормализованное название категории или None
    """
    for block_type, examples in HEADER_MAP.items():
        match, score, _ = process.extractOne(line.lower(), examples, scorer=fuzz.ratio)
        if score > 75:
            return block_type
    return None


def split_into_blocks_fuzzy(text: str) -> Dict[str, str]:
    """Разделяет текст резюме на блоки по заголовкам.

    Args:
        text: Полный текст резюме

    Returns:
        Dict[str, str]: Словарь блоков с текстом
    """
    blocks = {}
    current_block = "other"
    blocks[current_block] = []

    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue

        possible_header = normalize_header(clean)
        if possible_header:
            current_block = possible_header
            blocks[current_block] = []
        else:
            blocks.setdefault(current_block, []).append(clean)

    for key in blocks:
        blocks[key] = "\n".join(blocks[key])

    return blocks


def extract_keywords(text: str, lang: str = "ru", max_keywords: int = 50) -> List[str]:
    """Извлекает ключевые слова из текста.

    Args:
        text: Исходный текст
        lang: Язык текста
        max_keywords: Максимальное количество ключевых слов

    Returns:
        List[str]: Список извлеченных ключевых слов
    """
    kw_extractor = yake.KeywordExtractor(lan=lang, n=1, top=max_keywords)
    keywords = kw_extractor.extract_keywords(text)

    return [kw for kw, score in keywords]


def extract_base_info(text: str) -> Dict[str, Any]:
    """Извлекает базовую информацию о кандидате.

    Args:
        text: Текст резюме

    Returns:
        Dict[str, Any]: Словарь с данными (имя, возраст, город)
    """
    info = {}

    head_text = "\n".join(text.splitlines()[:10])
    doc = nlp(text)

    persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]
    if persons:
        info["full_name"] = persons[0]

    age_match = re.search(
        r"(?:возраст[:\s]*)?(\b\d{2}\b)\s*(?:лет|года?|г\.)?", head_text, re.IGNORECASE
    )
    if age_match:
        info["age"] = int(age_match.group(1))

    cities = [ent.text for ent in doc.ents if ent.label_ == "LOC"]
    if cities:
        info["city"] = cities[0]

    return info


def process_resume(file_path: str) -> Dict[str, Any]:
    """Обрабатывает файл резюме и извлекает структурированные данные.

    Args:
        file_path: Путь к файлу резюме

    Returns:
        Dict[str, Any]: Словарь с данными резюме, содержащий разделы:
            - base_info: базовая информация о кандидате
            - contacts: контактные данные
            - skills: навыки
            - experience: ключевые слова из опыта работы
            - projects: ключевые слова из проектов
            - other_sections: прочие разделы резюме
    """
    text = extract_text(file_path)
    blocks_fuzzy = split_into_blocks_fuzzy(text)

    skills_text = blocks_fuzzy.get("skills", "")
    experience_text = blocks_fuzzy.get("experience", "")
    projects_text = blocks_fuzzy.get("projects", "")

    contact_info = extract_contacts(text)
    base_info = extract_base_info(text)

    skills_keywords = extract_keywords(skills_text)
    experience_keywords = extract_keywords(experience_text)
    projects_keywords = extract_keywords(projects_text)

    resume_data = {
        "base_info": base_info,
        "contacts": contact_info,
        "skills": skills_keywords,
        "experience": experience_keywords,
        "projects": projects_keywords,
        "other_sections": {
            key: blocks_fuzzy[key]
            for key in blocks_fuzzy
            if key not in ["skills", "experience", "projects"]
        },
    }

    return resume_data


def save_to_json(data: Dict[str, Any], output_path: str) -> None:
    """Сохраняет данные в JSON-файл.

    Args:
        data: Данные для сохранения
        output_path: Путь к выходному файлу

    Returns:
        None
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def extract_brief(input_file: str, output_file: str) -> Dict[str, any] | None:
    """Извлекает данные из резюме и сохраняет их в JSON.

    Args:
        input_file: Путь к файлу резюме
        output_file: Путь для сохранения результата в формате json

    Returns:
        Dict[str, any]: Извлеченные данные из резюме

    Examples:
        >>> extract_brief("resume.pdf", "output.json")
    """
    try:
        result = process_resume(input_file)
        logging.info("Resume successfully processed.")
        return result
    except Exception as e:
        logging.error(f"Error: {e}")


if __name__ == "__main__":
    input_file = "resume2.pdf"  # Replace with your resume file path
    output_file = "resume2.json"

    try:
        result = process_resume(input_file)
        save_to_json(result, output_file)
        logging.info(f"Resume info has been saved to {output_file}")
    except Exception as e:
        logging.error(f"Error: {e}")
