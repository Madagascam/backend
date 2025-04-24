FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --without dev

COPY . .
RUN poetry install --no-interaction --no-ansi --without dev

CMD ["poetry", "run", "app/main.py"]
