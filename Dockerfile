FROM python:3.10.11-slim-buster

ARG APP_ENVIRONMENT

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # poetry:
    POETRY_VERSION=1.3.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    PATH="$PATH:/root/.local/bin"

WORKDIR /app

RUN pip install poetry==${POETRY_VERSION}

COPY pyproject.toml poetry.lock ./

# Only install dev dependencies if ENVIRONMENT=LOCAL
RUN if [ "${APP_ENVIRONMENT}" = "LOCAL" ]; \
    then poetry install --no-root --no-interaction --no-ansi; \
    else poetry install --no-root --no-dev --no-interaction --no-ansi; \
    fi

COPY . ./

CMD ["poetry", "run", "reshal-api"]
