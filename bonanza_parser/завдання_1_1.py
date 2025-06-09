from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc

from time import sleep
import random
import csv


# URL = 'https://www.bonanza.com'
# CATEGORY_URL = '/booths/browse_categories'


# cService = Service('C:/Users/kuzik/Desktop/bonanza_parser/chromedriver.exe')
# browser = uc.Chrome(service = cService)
# category_url = URL + CATEGORY_URL
# browser.get(category_url)
# sleep(8)
# try: browser.find_element(By.CLASS_NAME, 'needsclick.klaviyo-close-form.go2324193863.kl-private-reset-css-Xuajs1').click()
# except: pass

def get_category_list():
    categories = browser.find_elements(By.CLASS_NAME, 'title_item')
    category_list = []
    for category in categories:
        category_list.append(category.find_element(By.CLASS_NAME, 'accessible').get_attribute('href'))
    return category_list


def get_goods_page(category):
    browser.get(category)
    sleep(1)
    all_adds_in_category = browser.find_element(By.CLASS_NAME, 'see_all').find_element(By.CLASS_NAME, 'link_to_search')
    return all_adds_in_category.get_attribute('href')


def get_adds(category, quantity: int) -> list:
    page = get_goods_page(category)
    browser.get(page)
    sleep(2)
    with open('output.html', 'w', encoding='utf-8') as f:
        f.write(browser.page_source)
    
    adds = browser.find_elements(By.CLASS_NAME, 'search_result_item.browsable_item')
    if adds:
        pass
    else:
        adds = browser.find_elements(By.CLASS_NAME, 'list_style_row')
    
    adds_list = []
    for add in adds:
        link = add.find_element(By.CLASS_NAME, 'item_title').find_element(By.TAG_NAME, 'a')
        title = link.text
        href = link.get_attribute('href')
        adds_list.append({'title': title, 'href': href})
        if len(adds_list) == quantity:
            break

    return adds_list

def chenerate_id(digits):
    return ''.join([str(random.randint(0, 999)).zfill(digits) for _ in range(2)])

def get_bonanza_traits_and_details_dict(browser):
    traits_and_details = browser.find_elements(By.CLASS_NAME, 'extended_info_row')
    traits_and_details_dict = {}
    for trait in traits_and_details:
        label = trait.find_element(By.CLASS_NAME, 'extended_info_label').text 
        value = trait.find_element(By.CLASS_NAME, 'extended_info_value').text
        traits_and_details_dict[label] = value[:-2]
    return traits_and_details_dict



def collect_data(browser, title, href):
    price = browser.find_element(By.CLASS_NAME, 'item_price').text
    description = browser.find_element(By.CLASS_NAME, 'html_description').text
    picture = browser.find_element(By.CLASS_NAME, 'main_image_container').get_attribute('href')
    unic_id = chenerate_id(3) # if need more unic id, change 3 to 4 or 5
    traits_and_details_dict = get_bonanza_traits_and_details_dict(browser)
    bonanza_id = traits_and_details_dict.get('Item number', '')
    return Item(unic_id, bonanza_id, title, href, price, description, picture, **traits_and_details_dict)


class Item:
    def __init__(self, unic_id, bonanza_id, title, href, price, description, picture, **traits_and_details_dict):
        self.unic_id = unic_id
        self.bonanza_id = bonanza_id
        self.title = title
        self.href = href
        self.price = price
        self.description = description
        self.picture = picture
        self.traits_and_details = traits_and_details_dict

    def to_dict(self):
        return {
            "unic_id": self.unic_id,
            "bonanza_id": self.bonanza_id,
            "title": self.title,
            "href": self.href,
            "price": self.price,
            "description": self.description,
            "picture": self.picture,
            **self.traits_and_details
        }
    

def get_all_neccessary_data(category:int, quantity:int):
    items = []
    categories = get_category_list()
    for i in range(category):
        adds = get_adds(categories[i], quantity)
    
        for add in adds:
            browser.get(add['href'])
            sleep(2)
            items.append(collect_data(browser, add['title'], add['href']))
    return items

# print(get_all_neccessary_data(3, 5))

# items = get_all_neccessary_data(3, 5)
# print(items)
# filename = 'items.csv'

def save_items_to_csv(items, filename):
    # Формуємо динамічний список усіх можливих ключів
    all_fieldnames = set()
    for item in items:
        all_fieldnames.update(item.to_dict().keys())  # Додаємо всі ключі зі словників

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(all_fieldnames))
        writer.writeheader()
        for item in items:
            writer.writerow(item.to_dict())
# Викликаємо функцію
# save_items_to_csv(items, 'out_1.csv')

import numpy as np

# Зчитування CSV-файлу у масив
# data = np.genfromtxt('out_2.csv', delimiter=',', skip_header=1, dtype=float)

import pandas as pd

selected_columns = [
    "unic_id",
    "bonanza_id",
    "title",
    "href",
    "price",
    "description",
    "picture",
    # "Item number:",
]

df = pd.read_csv('out_2.csv', delimiter=',', engine='python')
filtered_df = df[selected_columns]

print(filtered_df)