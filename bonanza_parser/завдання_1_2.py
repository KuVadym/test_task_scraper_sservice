from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager

from functools import wraps
from time import sleep
import random
import csv


URL = 'https://www.bonanza.com'
CATEGORY_URL = '/booths/browse_categories'
CHROME_DRIVER_PATH = 'C:/Users/kuzik/Desktop/bonanza_parser/chromedriver.exe'
FILENAME = 'out_2.csv'
NUM_CATEGORIES = 3
QUANTITY = 5


def retry_on_exception(max_retries=3, retry_delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                    sleep(retry_delay)
            return None
        return wrapper
    return decorator


@retry_on_exception(max_retries=5, retry_delay=2)
def wait_for_element(browser, by, value, timeout=10):
    try:
        return WebDriverWait(browser, timeout).until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        return None



def get_category_url_list(browser) -> list:
    categories = browser.find_elements(By.CLASS_NAME, 'title_item')
    category_list = []
    for category in categories:
        category_list.append(category.find_element(By.CLASS_NAME, 'accessible').get_attribute('href'))
    return category_list


def get_goods_page(browser, category:int):
    browser.get(category)
    all_ads_link = wait_for_element(browser, By.CLASS_NAME, 'see_all')
    if all_ads_link:
        return all_ads_link.find_element(By.CLASS_NAME, 'link_to_search').get_attribute('href')
    return None


def get_adds(browser, category:int, quantity: int) -> list:
    page = get_goods_page(browser, category)
    if not page:
        return []
    
    browser.get(page)
    
    adds = browser.find_elements(By.CSS_SELECTOR, '.search_result_item.browsable_item, .list_style_row')
    adds_list = []

    for add in adds:
        try:
            link = add.find_element(By.CLASS_NAME, 'item_title').find_element(By.TAG_NAME, 'a')
            title = link.text
            href = link.get_attribute('href')
            adds_list.append({'title': title, 'href': href})
            if len(adds_list) >= quantity:
                break
        except NoSuchElementException:
            continue
    return adds_list

def generate_id(digits):
    return ''.join([str(random.randint(0, 999)).zfill(digits) for _ in range(2)])


def get_bonanza_traits_and_details_dict(browser) -> dict:
    traits_and_details = browser.find_elements(By.CLASS_NAME, 'extended_info_row')
    traits_and_details_dict = {}
    for trait in traits_and_details:
        try:
            label = trait.find_element(By.CLASS_NAME, 'extended_info_label').text 
            value = trait.find_element(By.CLASS_NAME, 'extended_info_value').text
            traits_and_details_dict[label] = value.strip()
        except NoSuchElementException:
            continue
    return traits_and_details_dict


def collect_data(browser, title:str, href:str):
    browser.get(href)
    sleep(2)
    try:
        price = browser.find_element(By.CLASS_NAME, 'item_price').text

        picture = browser.find_element(By.CLASS_NAME, 'main_image_container').find_element(By.TAG_NAME, 'a').get_attribute('href')
        traits_and_details_dict = get_bonanza_traits_and_details_dict(browser)

        bonanza_id = traits_and_details_dict.get('Item number:', '')
        try:
            description = browser.find_element(By.ID, 'descriptioncontent').text
        except NoSuchElementException:
            iframe = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "item_description_iframe")))
            browser.switch_to.frame(iframe)
            description = browser.find_element(By.TAG_NAME, "body").text
        
        return Item(generate_id(3), bonanza_id, title, href, price, description, picture, **traits_and_details_dict)
    except NoSuchElementException:
        return {'error': 'No such element'}


class Item:
    def __init__(self, unic_id, bonanza_id, title, href, price, description, picture, **traits):
        self.unic_id = unic_id
        self.bonanza_id = bonanza_id
        self.title = title
        self.href = href
        self.price = price
        self.description = description
        self.picture = picture
        self.traits = traits

    def to_dict(self):
        return {
            "unic_id": self.unic_id,
            "bonanza_id": self.bonanza_id,
            "title": self.title,
            "href": self.href,
            "price": self.price,
            "description": self.description,
            "picture": self.picture,
            **self.traits
        }
    

def get_all_neccessary_data(browser, num_categories:int, quantity:int)  -> list:
    items = []
    categories = get_category_url_list(browser)
    for i in range(num_categories):
        adds = get_adds(browser, categories[i], quantity)
    
        for add in adds:
            item = collect_data(browser, add['title'], add['href'])
            if item:
                items.append(item)
    return items




def save_items_to_csv(items:list, filename:str) -> None:

    all_fieldnames = set()
    for item in items:
        all_fieldnames.update(item.to_dict().keys())

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(all_fieldnames))
        writer.writeheader()
        for item in items:
            writer.writerow(item.to_dict())

def main(num_categories:int, quantity:int) -> None:
    with uc.Chrome(driver_executable_path=ChromeDriverManager().install()) as browser:
        category_url = URL + CATEGORY_URL
        browser.get(category_url)

        # wait_for_element(browser, By.CLASS_NAME, 'title_item', timeout=10)

        sleep(8)
        try: browser.find_element(By.CLASS_NAME, 'needsclick.klaviyo-close-form.go2324193863.kl-private-reset-css-Xuajs1').click()
        except: pass

        items = get_all_neccessary_data(browser, num_categories, quantity)
        print(items)
        save_items_to_csv(items, FILENAME)


if __name__ == '__main__':
    main(NUM_CATEGORIES, QUANTITY)