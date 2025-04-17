FROM python:3.10-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root
COPY . .
# Command to start the server
CMD ["python", "-m", "candidate"]
