EMAIL = 'Doere_in_Rome@gmail.com'
PASSWORD = 'SecurePassword123!'
URL ='https://www.luckycrush.live/'

import schedule
import time
import datetime
import os
import json

from bs4 import BeautifulSoup

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager

from database import user_repository


def save_cookies(driver):
    with open("cookies.json", "w") as file:
        json.dump(driver.get_cookies(), file)

def load_cookies(driver):
    if os.path.exists("cookies.json") and os.path.getsize("cookies.json") > 0:
        with open("cookies.json", "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        return driver
    else:
        return driver
    
def load_data(path):
    with open(path, "r") as file:
        data = json.load(file)
        return data


def update_time(path:str, model_name:str) -> tuple:
    if path:
        now = datetime.datetime.now().timestamp()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            data = load_data(path)
        except:
            data = None

        if today in data and model_name in data[today]:
            record = data[today][model_name]

            
            first_active = record.get('first_time_loged_in')
            last_active = record.get('last_time_loged_in')
            if (now - last_active) < 360:
                time_online = record.get('Time_online')
                time_online += 300
            else:
                time_online = record.get('Time_online')
        else: 
            first_active = now
            last_active = now
            time_online = 0
    return first_active, last_active, time_online


def parse_favorites(html):
    soup = BeautifulSoup(html, "html.parser")
    

    fav_section = soup.find("div", class_="fav-list-tabs")
    if not fav_section:
        return None
    

    active_tab = fav_section.find("div", class_="fav-list-tab-content-active")
    if not active_tab:

        return None


    fav_container = soup.find("ul", class_="feoNzP") 
    if not fav_container:
        return None

    favorites_data = {}

    favorite_items = fav_container.find_all("li")
    for idx, item in enumerate(favorite_items):
        try:

            model_id = item.get("data-id", f"fav_{idx + 1}")
            

            name_tag = item.find("span")
            model_name = name_tag.get_text(strip=True) if name_tag else "Unknown"
            
            first_active, last_active, time_online,  = update_time('favorites_data.json', model_name)
            

            favorites_data[model_name] = {
                'Model_name': model_name,
                'first_time_loged_in': first_active,
                'last_time_loged_in': last_active,
                'Time_online': time_online
            }
        except Exception as e:
            print(e)

    return favorites_data



def update_json_with_favorites(new_favorites: dict, json_filepath: str = "favorites_data.json") -> None:
    if os.path.exists(json_filepath) and os.path.getsize(json_filepath) > 0:
        try:
            with open(json_filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if today not in data:
        data[today] = {}
    
    for model_name, new_record in new_favorites.items():
        if model_name in data[today]:
            record = data[today][model_name]
            record["last_time_loged_in"] = new_record.get("last_time_loged_in", record["last_time_loged_in"])
            record["Time_online"] = new_record.get("Time_online", record["Time_online"])
        else:
            data[today][model_name] = new_record
    
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main() -> None:
    with uc.Chrome(driver_executable_path=ChromeDriverManager().install()) as driver:
        driver.get(URL)

        try:
            driver = load_cookies(driver)
            driver.refresh()  
        except FileNotFoundError as e:
            print(e)

        time.sleep(5)
        driver.find_element(By.CSS_SELECTOR, "div.fav-list-tab").click()

        save_cookies(driver)
        time.sleep(2)
        html = driver.page_source

        favorites = parse_favorites(html)
    
        if favorites is not None:
            update_json_with_favorites(favorites)
        else:
            print("Не вдалося отримати дані favorites.")

if __name__ == '__main__':
    main()