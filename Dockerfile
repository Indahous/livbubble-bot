FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Запускаем бота в фоне + dummy server на порту 8080
CMD (python bot.py &) && python -m http.server 8080
