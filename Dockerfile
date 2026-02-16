# --- Этап 1: Сборка и установка зависимостей ---
FROM ghcr.io/alexanderjkochnev/python:3.12 AS builder
WORKDIR /app
COPY requirements.txt .

# Устанавливаем системные зависимости для сборки (если нужны)
RUN apt-get update && \
    apt-get install -y libmagic-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем Python зависимости. Docker кэширует этот слой, если requirements.txt не меняется.
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Этап 2: Финальный образ (Runtime) ---
FROM ghcr.io/alexanderjkochnev/python:3.12-slim AS runtime
# Копируем системные библиотеки, если они были установлены на этапе сборки (например, libmagic-dev)
RUN apt-get update && \
    apt-get install -y libmagic1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Копируем установленные пакеты из первого этапа в путь пользователя второго этапа
COPY --from=builder /root/.local /root/.local

# Добавляем путь пользователя в PATH, чтобы приложения их видели
ENV PATH="/root/.local/bin:$PATH"

# Копируем ваш код приложения и конфигурационные файлы
COPY ./app ./app
COPY alembic.ini .
COPY .env .

ARG APP_PORT
ARG APP_HOST
ENV APP_PORT=${WEB_PORT}
ENV APP_HOST=${WEB_HOST}

EXPOSE $APP_PORT
# CMD ["uvicorn", "app.main:app", "--host", "$APP_HOST", "--port", "$APP_PORT", "--reload", "--loop", "uvloop"]
CMD ["sh", "-c", "uvicorn app.main:app --host $APP_HOST --port $APP_PORT --loop uvloop --workers 56"]
# CMD ["sh", "-c", "uvicorn app.main:app --host $APP_HOST --port $APP_PORT --reload --loop uvloop"]

