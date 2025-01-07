# syntax=docker/dockerfile:1
FROM python:3.13-alpine3.20 AS builder

# for building asyncmy on arm64
RUN apk update && apk add gcc libc-dev

RUN pip install --no-binary dulwich -C "--build-option=--pure" "poetry>=2.0.0"
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry-cache

WORKDIR /app
RUN touch README.md
COPY pyproject.toml poetry.lock LICENSE ./
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

FROM python:3.13-alpine3.20
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY ruyi_backend /app/ruyi_backend
WORKDIR /app
ENTRYPOINT [ "fastapi", "run", "ruyi_backend" ]
EXPOSE 8000

# LABELs are set in the build script for correctness across forks
