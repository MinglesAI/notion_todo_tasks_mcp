FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
COPY pyproject.toml .

# Создаем папку для исходного кода
COPY src/ ./src/

# Установка проекта в режиме разработки
RUN pip install --no-cache-dir -e .

# Порт для Streamable HTTP транспорта
EXPOSE 8000

# Создаем пустой .env файл для того, чтобы приложение не выдавало ошибку
# при запуске (реальные значения будут переданы через переменные окружения)
RUN touch .env

# Запуск сервера
CMD ["python", "-m", "notion_mcp", "--host", "0.0.0.0"] 