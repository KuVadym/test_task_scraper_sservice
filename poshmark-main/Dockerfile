FROM python:3.10-slim

# Устанавливаем необходимые зависимости
RUN apt-get update && apt-get install -y \
    nano \
    pkg-config \
    libmariadb-dev \
    cron \
    gcc

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости проекта
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install-deps
RUN playwright install

# Копируем все файлы проекта в контейнер
COPY . .

# Копируем cron задания
COPY cronjob /etc/cron.d/trigger_cron

# Даем права на выполнение cron файла
RUN chmod 0644 /etc/cron.d/trigger_cron

# Активируем cron задания
RUN crontab /etc/cron.d/trigger_cron

# Запуск cron и удержание контейнера активным
CMD ["cron", "-f"]
