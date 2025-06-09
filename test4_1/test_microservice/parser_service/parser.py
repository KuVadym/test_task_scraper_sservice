import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
import re
import os
import datetime

# Імпортуємо конфігураційні змінні
from parser_service import config


# Kuzyk_V add 31.03
from requests_html import HTMLSession
session = HTMLSession()
# Kuzyk_V fin adding







class ProductListExtractor:
    """
    Клас для вилучення інформації про товари з веб-сайту Bootbarn.
    Відповідає за отримання списку товарів з категорії та деталей окремого товару.
    """
    def __init__(self, base_url: str):
        """
        Ініціалізація екстрактора списку товарів.
        :param base_url: Базова URL-адреса сайту (береться з config.py).
        """
        self.base_url = base_url
        self.headers = config.HEADERS # Використовуємо заголовки з конфігурації

    def extract_products_count(self, category_url: str) -> int:
        """
        Отримує кількість товарів у категорії з HTML-сторінки.

        :param category_url: URL-адреса категорії.
        :return: Загальна кількість товарів у категорії або 0 у разі помилки.
        """
        try:
            # Виконуємо запит до сторінки категорії
            print(f"Отримання інформації про категорію: {category_url}")
            response = requests.get(category_url, headers=self.headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status() # Перевірка на HTTP помилки (4xx, 5xx)

            # Парсимо HTML сторінки за допомогою BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Шукаємо div з кількістю товарів за допомогою селектора з конфігурації
            product_count_div = soup.find("div", {"class": "product-hit-count mobile-hidden"})
            if not product_count_div:
                print("Не вдалося знайти блок з кількістю товарів.")
                return 0

            # Отримуємо текст і витягуємо число за допомогою регулярного виразу
            count_text = product_count_div.text.strip()
            count_match = re.search(r'(\d+)', count_text)
            if not count_match:
                print(f"Не вдалося виділити число з тексту: '{count_text}'")
                return 0

            total_products = int(count_match.group(1))
            return total_products

        except requests.exceptions.RequestException as e:
            print(f"Помилка запиту до сторінки категорії {category_url}: {e}")
            return 0
        except Exception as e:
            print(f"Неочікувана помилка при обробці кількості товарів для {category_url}: {e}")
            return 0

    def extract_product_info(self, product_url: str) -> dict:
        """
        Отримує детальну інформацію про товар за його URL-адресою.

        :param product_url: URL-адреса сторінки товару.
        :return: Словник з інформацією про товар (назва, ціна, бренд, характеристики тощо) або порожній словник у разі помилки.
        """
        try:
            print(f"Отримання інформації про товар: {product_url}")

            # Kuzyk V adding 31.03
            response = session.get(product_url, headers=self.headers, timeout=config.REQUEST_TIMEOUT)
            response.html.render(wait=1)
            # response = requests.get(product_url, headers=self.headers, timeout=config.REQUEST_TIMEOUT)
            # response.raise_for_status()
            # Парсимо HTML сторінки
            # soup = BeautifulSoup(response.text, 'html.parser')
            soup = BeautifulSoup(response.html.html, 'html.parser')
            # finish adding

            # Ініціалізуємо словник для зберігання інформації про товар
            product_info = {}

            # Знаходимо назву товару
            product_name_elem = soup.find("h1", {"class": "product-name"})
            if product_name_elem:
                # Очищуємо текст від зайвих символів
                product_info["name"] = product_name_elem.text.strip().replace("Product Name: \n", "")

            # Знаходимо ціну товару
            price_elem = soup.find("span", {"class": "price-original"})
            if price_elem:
                product_info["price"] = price_elem.text.strip().replace("\n Original Price", "")

            # Знаходимо бренд товару
            brand_elem = soup.find("div", {"class": "product-brand"})
            if brand_elem:
                url_for_brand = brand_elem.find("a")
                if url_for_brand:
                    product_info["brand"] = url_for_brand.text.strip()

            # Знаходимо номер (артикул) товару
            number_elem = soup.find("div", {"class": "product-number"})
            if number_elem:
                number = number_elem.find("span")
                if number:
                    product_info["number"] = number.text.strip()

            # Вилучення характеристик товару
            product_details = {}
            details_section = soup.find("div", {"class": "accordion product-features"})
            if details_section:
                # Спробуємо отримати повний HTML опис
                product_info_div = details_section.find("div", {"class": "product-info"})
                if product_info_div:
                    # Зберігаємо як HTML, так і простий текст (якщо потрібно)
                    html_content = str(product_info_div)
                    cleaned_html = re.sub(r'data-state="[^"]*"', '', html_content)
                    product_details["description_full_text_html"] = cleaned_html
                    

                # Вилучення характеристик зі списку (bullet points)
                feature_list = []
                features_ul = details_section.find("ul")
                if features_ul:
                    features = features_ul.find_all("li") # Використовуємо find_all для всіх елементів
                    for feature in features:
                        feature_text = feature.text.strip()
                        if feature_text:
                            feature_list.append(feature_text)

                    if feature_list:
                        product_details["features_list"] = feature_list

                # Спроба розпарсити структуровані характеристики з опису (секції з тегом <b>)
                if product_info_div:
                    bold_sections = product_info_div.find_all("b") # find_all зручніший тут
                    structured_features = {}
                    current_section_title = None

                    for bold_tag in bold_sections:
                        section_title = bold_tag.text.strip().rstrip(":")
                        # Отримуємо текст після поточного <b> до наступного <b> або кінця блоку
                        next_content = ""
                        next_node = bold_tag.next_sibling

                        while next_node and getattr(next_node, 'name', None) != "b":
                            if isinstance(next_node, str): # Якщо це текстовий вузол
                                next_content += next_node
                            elif getattr(next_node, 'name', None) != "br": # Ігноруємо теги <br>, але беремо текст з інших
                                next_content += next_node.get_text()
                            next_node = next_node.next_sibling

                        # Додаємо тільки якщо є заголовок і контент
                        if section_title and next_content.strip():
                            structured_features[section_title] = next_content.strip()

                    if structured_features:
                        product_details["structured_features"] = structured_features

            if product_details: # Додаємо секцію деталей, якщо вона не порожня
                product_info["product_details"] = product_details


            # Вилучення варіацій товару (кольори та розміри)
            variations = {}
            variations_section = soup.find("div", {"class": "product-variations"})
            if variations_section:
                # Отримуємо варіації кольорів
                color_section = variations_section.find("li", {"class": "attribute attribute-color"})
                if color_section:
                    colors = []
                    color_options = color_section.find_all("li", {"data-type": "color"})
                    for color_option in color_options:
                        color_data = {
                            "name": color_option.get("data-value", ""),
                            "selected": "selected" in color_option.get("class", []),
                            "id": color_option.get("data-id", "")
                        }

                        # Вилучаємо URL зображення кольору зі стилю
                        color_anchor = color_option.find("a", {"class": "swatchanchor"})
                        if color_anchor and color_anchor.get("style"):
                            style_attr = color_anchor.get("style", "")
                            url_match = re.search(r'url\((.*?)\)', style_attr)
                            if url_match:
                                color_data["image_url"] = url_match.group(1).strip("'\"") # Очищаємо від можливих лапок

                        colors.append(color_data)

                    if colors:
                        variations["colors"] = colors

                # Отримуємо варіації розмірів
                size_section = variations_section.find("li", {"class": "attribute-size"})
                if size_section:
                    sizes = []
                    size_options = size_section.find_all("li")
                    for size_option in size_options:
                        size_anchor = size_option.find("a", {"class": "swatchanchor"})
                        if size_anchor:
                            size_data = {
                                "name": size_anchor.get("data-size-name", ""),
                                "id": size_anchor.get("data-size-id", ""),
                                "selected": "selected" in size_option.get("class", []),
                                "available": "unselectable" not in size_option.get("class", [])
                            }

                            # Перевіряємо наявність на складі
                            stock_span = size_anchor.find("span", {"class": "stock-inner"})
                            if stock_span:
                                size_data["stock_status"] = stock_span.text.strip()

                            # Перевіряємо інформацію про доставку для розміру
                            shipping_span = size_anchor.find("span", {"class": "shipping"})
                            if shipping_span:
                                size_data["shipping_info"] = shipping_span.text.strip()

                            sizes.append(size_data)

                    if sizes:
                        variations["sizes"] = sizes

            if variations: # Додаємо секцію варіацій, якщо вона не порожня
                product_info["variations"] = variations

            # Вилучення інформації про доставку та повернення
            shipping_returns = {}
            shipping_section = soup.find("div", {"class": "accordion product-shipping-returns"})
            if shipping_section:
                # Вилучення інформації про повернення
                returns_message_elem = shipping_section.find("ul", {"class": "content-asset ca-product-returns-message"}).find("li")
                if returns_message_elem:
                    shipping_returns["returns"] = returns_message_elem.text.strip()

                # Вилучення обмежень доставки
                restrictions_section = shipping_section.find("div", {"class": "accordion-shipping-restrictions-section"})
                if restrictions_section:
                    restriction_items = restrictions_section.find_all("li", {"class": "product-shipping-restrictions"})
                    if restriction_items:
                        shipping_restrictions = []
                        for item in restriction_items:
                            restriction_info = {}
                            restriction_text = item.find("span")
                            if restriction_text:
                                restriction_info["text"] = restriction_text.text.strip()

                            # Знаходимо всі локації, до яких застосовується обмеження
                            locations = item.find_all("div", {"class": "restricted-location"})
                            if locations:
                                restriction_info["locations"] = [location.text.strip() for location in locations]

                            if restriction_info: # Додаємо, тільки якщо є хоч якась інформація
                                shipping_restrictions.append(restriction_info)

                        if shipping_restrictions:
                            shipping_returns["restrictions"] = shipping_restrictions

                # Перевірка обмежень перевізника
                carrier_restriction_elem = shipping_section.find("div", {"class": "content-asset ca-carrier-restriction-desc"})
                if carrier_restriction_elem:
                    shipping_returns["carrier_restriction"] = carrier_restriction_elem.text.strip()

                # Вилучення загального повідомлення про доставку
                shipping_message_elem = shipping_section.find("div", {"class": "content-asset ca-product-shipping-message"})
                if shipping_message_elem:
                    shipping_returns["message"] = shipping_message_elem.text.strip()

            if shipping_returns: # Додаємо секцію доставки/повернення, якщо вона не порожня
                product_info["shipping_returns"] = shipping_returns

            # Вилучення зображень товару
            product_images = []
            image_container = soup.find("div", {"class": "product-image-container-mobile"})
            if image_container:
                # Знаходимо всі теги img в контейнері
                images = image_container.find_all("img")
                for img in images:
                    src = img.get("src") or img.get("data-src") # Перевіряємо src та data-src
                    if src:
                        # Спроба отримати зображення високої роздільної здатності, замінивши параметри
                        if "sw=70&sh=70" in src:
                            src = src.replace("sw=70&sh=70", "sw=1980&sh=1980") # Замінюємо на більший розмір
                        elif "sw=" in src and "sh=" in src:
                            # Загальний випадок заміни параметрів розміру
                            src = re.sub(r'sw=\d+', 'sw=1980', src)
                            src = re.sub(r'sh=\d+', 'sh=1980', src)

                        # Додаємо абсолютний URL, якщо потрібно
                        if not src.startswith("http"):
                            src = urljoin(self.base_url, src)
                        product_images.append(src)

                # Видаляємо дублікати, зберігаючи порядок (для Python 3.7+)
                product_images = list(dict.fromkeys(product_images))

                if product_images:
                    product_info["images"] = product_images

            # Спроба отримати JSON дані про варіації з атрибута data-attributes (якщо є)
            try:
                variations_data_elem = soup.find("div", {"class": "product-variations"})
                if variations_data_elem and variations_data_elem.get("data-attributes"):
                    variations_json_str = variations_data_elem["data-attributes"]
                    variations_data = json.loads(variations_json_str)
                    if variations_data:
                        product_info["variations_data_json"] = variations_data # Додаємо ці дані
            except json.JSONDecodeError as e:
                print(f"Помилка розбору JSON даних про варіації для {product_url}: {e}")
            except Exception as e:
                print(f"Неочікувана помилка при обробці JSON варіацій для {product_url}: {e}")

            return product_info

        except requests.exceptions.RequestException as e:
            print(f"Помилка запиту до сторінки товару {product_url}: {e}")
            return {} # Повертаємо порожній словник у разі помилки запиту
        except Exception as e:
            print(f"Неочікувана помилка при обробці даних товару {product_url}: {e}")
            # Тут можна додати логування помилки для детального аналізу
            # import traceback
            # print(traceback.format_exc())
            return {} # Повертаємо порожній словник у разі іншої помилки

    def extract_product_list(self, category_url: str) -> dict:
        """
        Отримує повний список товарів з категорії, обробляючи пагінацію шляхом
        запиту всіх товарів на одній сторінці (якщо сайт це підтримує).

        :param category_url: URL-адреса категорії.
        :return: Словник, де ключ - URL товару, значення - словник з інформацією про товар.
        """
        products_dict = {}

        # Спочатку отримуємо загальну кількість товарів у категорії
        total_products = self.extract_products_count(category_url)
        if total_products == 0:
            print(f"Не вдалося отримати кількість товарів або їх немає для категорії: {category_url}")
            return products_dict # Повертаємо порожній словник, якщо товарів немає або сталася помилка

        # Формуємо URL для запиту всіх товарів одразу
        # Додаємо параметри start (кількість товарів на сторінці)
        # Встановлюємо start=total_products, щоб отримати всі товари

        if "?" in category_url:
            # Якщо URL вже має параметри, додаємо нові через &
            all_products_url = f"{category_url}&start={total_products}"
        else:
            # Якщо параметрів немає, додаємо перший через ?
            all_products_url = f"{category_url}?start={total_products}"

        try:
            print(f"Отримання всіх товарів ({total_products}) з: {all_products_url} може зайняти багато часу")
            # Використовуємо довший таймаут, оскільки сторінка може бути великою
            response = requests.get(all_products_url, headers=self.headers, timeout=config.LONG_REQUEST_TIMEOUT)
            response.raise_for_status()

            # Парсимо HTML сторінки
            soup = BeautifulSoup(response.text, 'html.parser')

            # Знаходимо список товарів за селектором з конфігурації
            product_list_ul = soup.find("ul", {"id": "search-result-items"})
            if not product_list_ul:
                print(f"Не вдалося знайти список товарів на сторінці: {all_products_url}")
                return products_dict

            # Знаходимо всі елементи списку товарів (карточки товарів)
            product_items = product_list_ul.find_all("li", {"class": "grid-tile"})
            print(f"Знайдено {len(product_items)} карточок товарів на сторінці.")
            if len(product_items) < total_products:
                 print(f"Увага: Отримано {len(product_items)} товарів, хоча очікувалося {total_products}. Можливо, є обмеження на параметр 'sz'.")


            # Проходимо по кожному товару в списку
            for item_index, item in enumerate(product_items):
                # Знаходимо посилання на сторінку товару
                product_link_tag = item.find("a", {"class": "name-link"})
                if not product_link_tag:
                    print(f"Попередження: Не знайдено посилання на товар в елементі {item_index+1}")
                    continue # Переходимо до наступного елемента

                product_url = product_link_tag.get("href", "")
                if not product_url:
                    print(f"Попередження: Порожнє посилання на товар в елементі {item_index+1}")
                    continue

                # Формуємо повну URL-адресу, якщо вона відносна
                if not product_url.startswith("http"):
                    product_url = urljoin(self.base_url, product_url)

                # Викликаємо метод для отримання детальної інформації про цей товар
                product_info = self.extract_product_info(product_url)

                if product_info: # Додаємо товар, тільки якщо вдалося отримати інформацію
                    products_dict[product_url] = product_info
                else:
                    print(f"Попередження: Не вдалося отримати інформацію для товару: {product_url}")

                # Робимо невелику затримку між запитами до сторінок товарів
                print(f"Оброблено товар {item_index+1}/{len(product_items)}. Затримка {config.SLEEP_TIME_BETWEEN_PRODUCTS} сек...")
                time.sleep(config.SLEEP_TIME_BETWEEN_PRODUCTS)

            print(f"Завершено обробку товарів.")
            return products_dict

        except requests.exceptions.RequestException as e:
            print(f"Помилка запиту до сторінки зі всіма товарами {all_products_url}: {e}")
            return products_dict # Повертаємо те, що встигли зібрати
        except Exception as e:
            print(f"Неочікувана помилка при обробці списку товарів для {all_products_url}: {e}")
            # import traceback
            # print(traceback.format_exc())
            return products_dict # Повертаємо те, що встигли зібрати


# =============================================================================
# Клас для отримання посилань на категорії сайту
# =============================================================================
class CategoryExtractor:
    """
    Клас для вилучення ієрархії категорій та їх URL-адрес з головної сторінки сайту.
    """
    def __init__(self, base_url: str):
        """
        Ініціалізація екстрактора категорій.
        :param base_url: Базова URL-адреса сайту (береться з config.py).
        """
        self.base_url = base_url
        self.headers = config.HEADERS # Використовуємо заголовки з конфігурації

    def extract_categories(self) -> dict:
        """
        Отримує посилання на категорії з головного меню сайту.
        Парсить багаторівневе меню та повертає словник.

        :return: Словник у форматі {назва_категорії: посилання}, де назва включає шлях (напр., "Головна > Підкатегорія").
                 Повертає порожній словник у разі помилки.
        """
        try:
            print(f"Отримання категорій з головної сторінки: {self.base_url}")
            # Виконуємо запит до головної сторінки
            response = requests.get(self.base_url, headers=self.headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()  # Перевіряємо чи запит успішний

            # Парсимо HTML сторінки
            soup = BeautifulSoup(response.text, 'html.parser')

            categories_dict = {} # Словник для зберігання результатів
            # Знаходимо головний контейнер меню категорій
            main_menu = soup.find("ul", {"class": "menu-category", "role": "menubar"})

            if main_menu:
                # Знаходимо всі пункти меню першого рівня
                menu_items = main_menu.find_all("li", {"role": "menuitem"}, recursive=False) # Шукаємо тільки прямих нащадків

                for item in menu_items:
                    # Отримуємо назву головної категорії (пункту першого рівня)
                    main_link = item.find("a", {"class": "has-sub-menu"})
                    main_category_name = "Невідома головна категорія" # Значення за замовчуванням
                    main_category_url = None

                    if main_link:
                        span = main_link.find("span")
                        if span:
                            main_category_name = span.text.strip()

                        # Перевіряємо, чи має головна категорія власне посилання
                        href = main_link.get("href", "")
                        if href and href.strip() and href != "#": # Ігноруємо порожні посилання та заглушки
                            main_category_url = urljoin(self.base_url, href) # Робимо URL абсолютним
                            categories_dict[main_category_name] = main_category_url # Додаємо головну категорію

                    # Знаходимо блок з підкатегоріями (рівень 2)
                    subcategories_div = item.find("div", {"class": "level-2"})
                    if subcategories_div:
                        # Обробляємо навігаційні посилання в колонках
                        nav_links_div = subcategories_div.find("div", {"class": "nav-links"})
                        if nav_links_div:
                            nav_columns = nav_links_div.find_all("div", {"class": "navigation-column"})
                            for column in nav_columns:
                                # Шукаємо заголовок колонки (якщо є)
                                header = column.find("h4", {"class": "nav-list-header"})
                                column_title = header.text.strip() if header else ""

                                # Знаходимо всі списки посилань у колонці
                                ul_lists = column.find_all("ul", {"class": "menu-horizontal"})
                                for ul in ul_lists:
                                    # Знаходимо всі посилання в кожному списку
                                    links = ul.find_all("a")
                                    for link in links:
                                        href = link.get("href", "")
                                        link_text = link.text.strip()
                                        if href and href.strip() and href != "#" and link_text:
                                            # Формуємо повну назву категорії (з батьківськими)
                                            if column_title:
                                                category_name = f"{main_category_name} > {column_title} > {link_text}"
                                            else:
                                                category_name = f"{main_category_name} > {link_text}"

                                            # Форматуємо URL
                                            category_url = urljoin(self.base_url, href)
                                            categories_dict[category_name] = category_url

                        # Обробляємо зображення-посилання в навігації (якщо є)
                        nav_image_div = subcategories_div.find("div", {"class": "nav-image"})
                        if nav_image_div:
                            image_link = nav_image_div.find("a")
                            if image_link:
                                href = image_link.get("href", "")
                                if href and href.strip() and href != "#":
                                    # Форматуємо URL
                                    category_url = urljoin(self.base_url, href)

                                    # Використовуємо підпис зображення або запасний текст
                                    image_title_span = image_link.find("span", {"class": "image-title"})
                                    img_text = image_title_span.text.strip() if image_title_span else "Посилання з зображення"

                                    category_name = f"{main_category_name} > {img_text}"
                                    categories_dict[category_name] = category_url
            else:
                print("Помилка: Головне меню навігації (ul.menu-category) не знайдено на сторінці.")

            print(f"Знайдено та оброблено категорій: {len(categories_dict)}")
            return categories_dict

        except requests.exceptions.RequestException as e:
            print(f"Помилка під час запиту до головної сторінки {self.base_url}: {e}")
            return {}
        except Exception as e:
            print(f"Неочікувана помилка при вилученні категорій: {e}")
            # import traceback
            # print(traceback.format_exc())
            return {}

# =============================================================================
# Основний клас парсера Bootbarn, що об'єднує компоненти
# =============================================================================
class BootbarnParser:
    """
    Головний клас парсера, який керує процесом збору категорій та товарів.
    Використовує CategoryExtractor для отримання категорій та ProductListExtractor для товарів.
    """
    def __init__(self, base_url: str, categories_file: str = config.CATEGORIES_FILE, products_dir: str = config.PRODUCTS_DIR):
        """
        Ініціалізація парсера.
        :param base_url: Базова URL-адреса сайту (з config.py).
        :param categories_file: Шлях до файлу для збереження категорій (з config.py).
        :param products_dir: Шлях до директорії для збереження файлів товарів (з config.py).
        """
        self.base_url = base_url
        self.categories_file = categories_file
        self.products_dir = products_dir
        self.category_extractor = CategoryExtractor(self.base_url)
        self.product_extractor = ProductListExtractor(self.base_url)

        # Створюємо директорію для продуктів, якщо її немає
        if not os.path.exists(self.products_dir):
            try:
                os.makedirs(self.products_dir)
                print(f"Створено директорію для збереження товарів: {self.products_dir}")
            except OSError as e:
                print(f"Помилка створення директорії {self.products_dir}: {e}")
                # Вирішуємо, чи продовжувати роботу, якщо директорію створити не вдалося
                # У цьому випадку, спробуємо зберегти в поточну директорію
                self.products_dir = "."


    def save_to_json(self, data: dict, filename: str):
        """
        Універсальна функція для збереження даних у JSON файл.
        :param data: Словник з даними для збереження.
        :param filename: Повний шлях до файлу для збереження.
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Використовуємо ensure_ascii=False для коректного збереження українських літер
                # indent=4 робить файл читабельним
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Дані успішно збережено у файл: {filename}")
        except IOError as e:
            print(f"Помилка запису у файл {filename}: {e}")
        except Exception as e:
            print(f"Неочікувана помилка при збереженні у JSON файл {filename}: {e}")

    def save_categories_to_json(self, categories: dict):
        """
        Зберігає отриманий словник категорій у JSON файл.
        Використовує ім'я файлу з конфігурації (`config.CATEGORIES_FILE`).
        :param categories: Словник з категоріями {назва: url}.
        """
        if not categories:
            print("Словник категорій порожній, збереження скасовано.")
            return
        print(f"Збереження {len(categories)} категорій у файл {self.categories_file}...")
        self.save_to_json(categories, self.categories_file)

    def save_products_to_json(self, category_name: str, products: dict):
        """
        Зберігає товари вказаної категорії у JSON файл.
        Ім'я файлу генерується на основі назви категорії та містить мітку часу.
        Файл зберігається у директорію, вказану в `config.PRODUCTS_DIR`.

        :param category_name: Назва категорії (використовується для імені файлу).
        :param products: Словник з інформацією про товари {url: product_info}.
        :return: Повертає повний шлях до збереженого файлу або None у разі помилки.
        """
        if not products:
            print(f"Список товарів для категорії '{category_name}' порожній, збереження скасовано.")
            return None

        try:
            # Формуємо безпечне ім'я файлу з назви категорії:
            # 1. Замінюємо роздільники шляху '>' на '-'.
            # 2. Видаляємо символи, неприпустимі для імен файлів (крім букв, цифр, _, -).
            # 3. Замінюємо пробіли на підкреслення.
            # 4. Обрізаємо зайві пробіли/дефіси на початку/кінці.
            safe_category_name = re.sub(r'[^\w\s-]', '', category_name.replace('>', '-')).strip()
            safe_category_name = re.sub(r'[-\s]+', '_', safe_category_name)

            # Додаємо мітку часу для унікальності файлу
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_category_name}_{timestamp}.json"
            full_path = os.path.join(self.products_dir, filename)

            # Додаємо метадані до вихідного файлу для кращого розуміння даних
            metadata = {
                "source_category_name": category_name,
                "parsed_category_url": list(products.keys())[0].split('?')[0] if products else "N/A", # Приблизний URL категорії
                "parser_timestamp": timestamp,
                "total_products_saved": len(products),
                "parse_datetime_utc": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            }

            # Об'єднуємо метадані та словник продуктів
            output_data = {
                "metadata": metadata,
                "products": products # продукти йдуть як є: {url: info}
            }

            print(f"Збереження {len(products)} товарів у файл {full_path}...")
            self.save_to_json(output_data, full_path)
            return full_path

        except Exception as e:
            print(f"Помилка при підготовці до збереження товарів категорії '{category_name}': {e}")
            return None

    def get_all_categories(self):
        """
        Запускає процес парсингу категорій та зберігає результати у JSON файл.
        :return: Словник з категоріями {назва: url} або порожній словник у разі помилки.
        """
        # Отримуємо список категорій
        categories = self.category_extractor.extract_categories()

        if not categories:
            print("Не вдалося отримати категорії. Подальша обробка неможлива.")
            return {}

        # Зберігаємо категорії у файл
        self.save_categories_to_json(categories)

        print(f"Збережено {len(categories)} категорій.")
        return categories

    def get_products_from_category(self, category_name: str, category_url: str):
        """
        Отримує список товарів з вказаної категорії та зберігає їх у JSON файл.
        :param category_name: Назва категорії (для імені файлу та логування).
        :param category_url: URL-адреса категорії для парсингу.
        :return: Словник з товарами {url: info} або порожній словник у разі помилки.
        """
        products = self.product_extractor.extract_product_list(category_url)

        if products:
            # Зберігаємо знайдені товари у файл
            self.save_products_to_json(category_name, products)
        else:
            print(f"Не знайдено товарів або сталася помилка при парсингу категорії: '{category_name}'")
        return products


# =============================================================================
# Головна функція для запуску парсера
# =============================================================================
def main(category_name:str):
    """
    Головна функція, яка ініціалізує парсер та керує процесом парсингу.
    Приклад: завантажує категорії з файлу (або парсить їх, якщо файлу немає)
    і потім парсить товари для однієї конкретної категорії.
    """
    print("Запуск парсера Bootbarn...")
    # Ініціалізуємо головний клас парсера, використовуючи налаштування з config.py
    parser = BootbarnParser(
        base_url=config.BASE_URL,
        categories_file=config.CATEGORIES_FILE,
        products_dir=config.PRODUCTS_DIR
    )

    categories = {}
    # Спробуємо завантажити категорії з файлу
    try:
        if os.path.exists(parser.categories_file):
            with open(parser.categories_file, "r", encoding="utf-8") as f:
                categories = json.load(f)
            print(f"Завантажено {len(categories)} категорій з файлу: {parser.categories_file}")
        else:
             print(f"Файл категорій '{parser.categories_file}' не знайдено. Запускаємо парсинг категорій...")
             categories = parser.get_all_categories()

    except json.JSONDecodeError:
        print(f"Помилка читання JSON з файлу '{parser.categories_file}'. Файл може бути пошкоджено.")
        print("Спробуємо отримати категорії з сайту...")
        categories = parser.get_all_categories()
    except IOError as e:
        print(f"Помилка доступу до файлу категорій '{parser.categories_file}': {e}")
        print("Спробуємо отримати категорії з сайту...")
        categories = parser.get_all_categories()
    except Exception as e:
        print(f"Неочікувана помилка при завантаженні/отриманні категорій: {e}")

    # Якщо категорії успішно отримані (з файлу або парсингом)
    if categories:
        # === Приклад: Парсинг товарів для ОДНІЄЇ конкретної категорії ===
        target_category_name = category_name # "SALE > Shop by category > Men's Sale Hats" # Приклад категорії

        if target_category_name in categories:
            target_category_url = categories[target_category_name]
            print(f"\nЗнайдено URL для цільової категорії '{target_category_name}': {target_category_url}")

            # Запускаємо парсинг товарів для цієї категорії
            parser.get_products_from_category(target_category_name, target_category_url)
        else:
            print(f"\nПомилка: Категорія '{target_category_name}' не знайдена у списку завантажених/отриманих категорій.")
            print("Можливі причини: неправильна назва категорії, або вона не була знайдена під час парсингу меню.")
            if len(categories) < 20: # Якщо категорій не дуже багато, виведемо їх для допомоги
                print("\nДоступні категорії:")
                for name in categories.keys():
                    print(f"- {name}")

    else:
        print("Не вдалося отримати список категорій. Парсинг товарів неможливий.")

    print("\nРоботу парсера завершено.")


# Точка входу: цей блок виконається, якщо скрипт запущено напряму
if __name__ == "__main__":
    main()