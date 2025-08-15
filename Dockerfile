# Dockerfile — Telegram Bot + dummy server
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

# Запускаем бота в фоне + dummy server на порту 8080
CMD (python bot.py &) && python -m http.server 8080
