# CandidateMatcher
*Для кода ревью в проекте использовался CodeRabbit и Copilot.*
Документация на Sphinx: [Docs](https://candidatematcher.readthedocs.io/ru/latest/)
## Описание
Проект предназначен для автоматической обработки резюме, извлечения ключевых данных и
оценки соответствия кандидата вакансиям с использованием языковых моделей.
Сначала происходит извлечение данных из резюме, затем осуществляется
сопоставление кандидатов с вакансиями на основе их навыков и требований вакансий. Для работы
проекта вместе с Ollama требуется как минимум 4гб видеопамяти. Для работы
контейнера с gpu для быстрой работы необходим [Nvidia Toolkit](https://developer.nvidia.com/cuda-toolkit). Если
нет возможности использовать GPU, то в файле docker-compose нужно удалить строчку:
`runtime: nvidia`.
В будущем для улучшения масштабирования вместо ollama можно будет использовать vllm.

## Дополнительная настройка запуска
Пример извлечённых данных из резюме представлен в файле `data/example.json`. \
Предоставленные вакансии представлены в файле `data/vacancies.json`. \
Чтобы добавить новые вакансии, в json файле должны быть указаны следующие поля: название вакансии, описание и компетенции.
Компетенции должны содержать как минимум один блок навыков (например, `общие_компетенции`),
в котором будет список из компетенций, содержащий название компетенции и необходимый уровень. Например: \
`{"название": "Методы машинного обучения", "уровень": 2},`. \
В docker-compose файле можно изменить модель, которая будет использоваться.
## Запуск
Для запуска проекта достаточно выполнить команду:
```bash
docker-compose up --build
```
После этого порту `8000` и с эндпоинтом `/candidate_match` можно отправлять запрос с
резюме в виде docx, pdf и txt форматах, после чего будет возвращён
json с результатами. Результат будет содержать два поля: поле с подходящей
вакансией (если хоть одна подходит) `vacancy`, поле, на сколько процентов
кандидат подходит: `percentage`. За отсутствующие навыки будут вычитаться проценты.
поле с описанием и рассуждением `explaining` и рекомендации `recommendations`.

## Более подробное описание технологий

## Основные функции
- **Парсинг резюме** (PDF/DOCX/TXT):
  - Извлечение контактов (email, телефон, соцсети)
  - Автоматическое определение блоков (навыки, опыт, образование)
  - Распознавание базовой информации (ФИО, возраст, город)
- **Анализ данных**:
  - Извлечение ключевых слов с помощью YAKE
  - Нейросетевая оценка соответствия вакансиям (Ollama)
  - Генерация рекомендаций по обучению

### Технологии
**Обработка документов**:
- `pdfplumber`
- `python-docx`

**NLP**:
- `spaCy` + `ru_core_news_md` (NER)
- `YAKE` (ключевые слова)
- `RapidFuzz` (fuzzy-сопоставление)

**ML/LLM**:
- `Ollama` (локальные LLM)
- Кастомные промпты
- JSON Schema валидация

**Инфраструктура**:
- Poetry
- Логирование
- Конфигурация через ENV
