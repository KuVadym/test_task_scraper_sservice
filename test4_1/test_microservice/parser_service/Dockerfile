FROM python:3.10
WORKDIR /
COPY  . .
RUN pip install requirements.txt
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]

FROM python:3.10

# Встановлюємо робочу директорію
WORKDIR /app

# Встановлюємо залежності для Chromium
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango1.0-0 \
    libpangocairo-1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо файли проекту
COPY parser_service/ /app

# Створюємо віртуальне середовище та встановлюємо залежності
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install -r requirements.txt

# Виправлення файлів після встановлення бібліотек
RUN sed -i "s/from lxml.html.clean import Cleaner/from lxml_html_clean import Cleaner/" /venv/lib/python3.10/site-packages/requests_html.py && \
    sed -i "s/__chromium_revision__ = .*/__chromium_revision__ = '1263111'/" /venv/lib/python3.10/site-packages/pyppeteer/__init__.py

# Вказуємо команду для запуску мікросервісу
CMD ["/venv/bin/python", "run.py"]
