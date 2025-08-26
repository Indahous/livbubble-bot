# Dockerfile — Telegram Bot (FastAPI + aiogram)

FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY . .

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 8080

# Запускаем бота
CMD ["uvicorn", "bot:app", "--host", "0.0.0.0", "--port", "8080"]
