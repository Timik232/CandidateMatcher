import json
import logging
import os
import re

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


def extract_text_from_pdf(file_path: str):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    pdf.close()
    return text


def extract_text_from_docx(file_path: str):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


def extract_text(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_contacts(text: str):
    contacts = {}

    # Email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        contacts["email"] = email_match.group(0)

    # Phone
    phone_match = re.search(
        r"(?:(?:8|\+7)[\- ]?)?(?:\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}", text
    )
    if phone_match:
        contacts["phone"] = phone_match.group(0)

    # Telegram
    telegram_match = re.search(r"@[\w\d_]+", text)
    if telegram_match:
        tag = telegram_match.group(0)
        if not re.match(r"[\w\.-]+@[\w\.-]+\.\w+", tag):
            contacts["telegram"] = tag

    # GitHub
    github_match = re.search(r"(https?://)?(www\.)?github\.com/[^\s\n]+", text)
    if github_match:
        contacts["github"] = github_match.group(0)

    # VK
    vk_match = re.search(
        r"(https?://)?(www\.)?(vk\.com/[^\s\n]+|вконтакте|вк|vk@[\w\d_]+)",
        text,
        re.IGNORECASE,
    )
    if vk_match:
        contacts["vk"] = vk_match.group(0)

    # hh.ru
    hh_match = re.search(r"(https?://)?(www\.)?hh\.ru/[^\s\n]+", text)
    if hh_match:
        contacts["hh"] = hh_match.group(0)

    # LinkedIn
    linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/[^\s\n]+", text)
    if linkedin_match:
        contacts["linkedin"] = linkedin_match.group(0)

    return contacts


def normalize_header(line: str):
    for block_type, examples in HEADER_MAP.items():
        match, score, _ = process.extractOne(line.lower(), examples, scorer=fuzz.ratio)
        if score > 75:
            return block_type
    return None


def split_into_blocks_fuzzy(text: str):
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


def extract_keywords(text: str, lang: str = "ru", max_keywords: int = 50):
    kw_extractor = yake.KeywordExtractor(lan=lang, n=1, top=max_keywords)
    keywords = kw_extractor.extract_keywords(text)

    return [kw for kw, score in keywords]


def extract_base_info(text: str):
    info = {}

    head_text = "\n".join(text.splitlines()[:10])
    doc = nlp(text)

    # Имя
    persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]
    # clean_persons = [p for p in persons if all(c.isalpha() or c.isspace() for c in p) and len(p.split()) <= 3]
    if persons:
        info["full_name"] = persons[0]

    # Возраст
    age_match = re.search(
        r"(?:возраст[:\s]*)?(\b\d{2}\b)\s*(?:лет|года?|г\.)?", head_text, re.IGNORECASE
    )
    if age_match:
        info["age"] = int(age_match.group(1))

    # Город — из GPE
    cities = [ent.text for ent in doc.ents if ent.label_ == "LOC"]
    if cities:
        info["city"] = cities[0]

    return info


def process_resume(file_path: str):
    text = extract_text(file_path)
    blocks_fuzzy = split_into_blocks_fuzzy(text)

    skills_text = blocks_fuzzy.get("skills", "")
    experience_text = blocks_fuzzy.get("experience", "")
    projects_text = blocks_fuzzy.get("projects", "")

    contact_info = extract_contacts(text)
    base_info = extract_base_info(text)  # передаём блоки

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


def save_to_json(data, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    input_file = "resume2.pdf"  # Replace with your resume file path
    output_file = "resume2.json"

    try:
        result = process_resume(input_file)
        save_to_json(result, output_file)
        logging.info(f"Resume info has been saved to {output_file}")
    except Exception as e:
        logging.error(f"Error: {e}")
