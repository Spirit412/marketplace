FROM python:3.12-alpine

ARG APP_PORT=8170
ENV APP_PORT=${APP_PORT}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src

RUN pip install --upgrade pip && \
    pip install --upgrade poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml pyproject.toml
RUN poetry install --no-root

COPY src/ src/
COPY alembic.ini alembic.ini
