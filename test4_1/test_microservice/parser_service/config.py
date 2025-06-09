# config.py

"""
Файл конфігурації для парсера Bootbarn.
Містить базові налаштування, такі як URL, заголовки запитів та імена файлів.
"""

# Базова URL-адреса сайту для парсингу
BASE_URL = "https://www.bootbarn.com/"

# Заголовки HTTP-запитів для імітації браузера та уникнення блокування
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5", # Можна змінити на uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7 якщо потрібно
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Ім'я файлу для збереження списку категорій
CATEGORIES_FILE = "categories.json"

# Директорія для збереження файлів з товарами
PRODUCTS_DIR = "products"

# Максимальний час очікування відповіді від сервера (в секундах)
REQUEST_TIMEOUT = 30  # Стандартний таймаут для більшості запитів
LONG_REQUEST_TIMEOUT = 600 # Таймаут для потенційно довгих запитів (наприклад, завантаження всіх товарів категорії)

# Час затримки між запитами до сторінок товарів (в секундах), щоб зменшити навантаження на сервер
SLEEP_TIME_BETWEEN_PRODUCTS = 0.3
