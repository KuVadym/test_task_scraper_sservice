WEBSITE  = 'poshmark.com'


# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager

import seleniumwire.undetected_chromedriver as uc


from seleniumwire import webdriver

import json
import time
import random
import os


# CHROME_DRIVER_PATH = 'C:/Users/kuzik/Desktop/bonanza_parser/chromedriver.exe'
# PROXY_IPS = ["38.153.152.244", '83.97.79.222', '83.97.79.222', '91.231.186.249', '91.231.186.249:1080']
# PROXY_PORT = ['9594', '1080', '1080', '1080', '1080']
# PROXY_PASSWORD = ['d1bz5lnvx4l6', '13qhzmjnxgp', '1rvihabkgmp', '1l6h5ssvjit', 'asnt9kzo47']
# PROXY_USERNAME = ['yjjmyydd', '1nhfci7k941', '1ioidb177hp', '1043l0846jt', '1mbl19uqnvb']

PROXY_ADDRESSES = ['socks5://pmmpa9g38j:xtpekbo5c3@213.109.192.192:1080',
'socks5://z5wwbo590n:13xjr77blb7@213.109.192.192:1080',
'socks5://1rwor64mpwx:z1jsdgahm7@62.106.66.109:1080',
                   ]
data = {
    "title": "Sample Product Title",             # Заголовок оголошення (що продається)
    "description": "Це приклад опису товару. Тут можна зазначити такі деталі, як бренд, розмір, колір, стан, матеріал тощо.", 
    "price": "50",                                 # Ціна товару
    "brand": "Sample Brand",                       # Бренд (якщо потрібно)
    "category": "Women",                           # Категорія, яка відповідає одному з варіантів у випадаючому меню 
    "subcategory": "Dresses",                      # Підкатегорія (опціонально)
    "quantity": "Single Item",                     # Кількість (може бути: "Single Item" або "Multi Item")
    "size": "M",                                   # Розмір (якщо застосовується)
    "photos": ["path/to/photo1.jpg", "path/to/photo2.jpg"],  # Шлях до фото (опціонально, може бути список шляхів)
    # "video": "path/to/video.mp4"                 # URL або шлях до відео (опціонально)
}

def get_proxy(proxy_num: int) -> str:
    '''
        Args:
            proxy_num (int): The number used to retrieve the proxy address.
        You need to have proxy data in the global variables such as :
            PROXY_ADDRESSES, PROXY_PORT, PROXY_PASSWORD, PROXY_USERNAME
        or
            PROXY_ADDRESS 
    
        Returns:
            Str: Proxy address ready to use
    '''
    try:
        proxy = f"socks5://{PROXY_USERNAME[proxy_num]}:{PROXY_PASSWORD[proxy_num]}@{PROXY_ADDRESSES[proxy_num]}:{PROXY_PORT[proxy_num]}"
    except Exception as e:
        print(f"Error in get_proxy function: {e}")
    try:
        proxy = PROXY_ADDRESSES[proxy_num]
    except Exception as e:
        print(f"Error in get_proxy function: {e}")

    return proxy


def init_web_driver_with_auth(proxy_num:int):
    """
        Initializes a Chrome WebDriver with a specified proxy.
        Args:
            proxy_num (int): The number used to retrieve the proxy address.
        Returns:
            WebDriver: An instance of Chrome WebDriver configured with the specified proxy.
    """
    proxy_address = get_proxy(proxy_num)
    proxy_options = {
    'proxy': {
        'https': f'{proxy_address}',
    }
}
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')  
    chrome_options.add_argument('--no-sandbox')  
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-3d-apis")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--disable-webrtc")

    driver = uc.Chrome(options=chrome_options, seleniumwire_options = proxy_options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "Referer": "https://example.com/previous_page"
        }
    })

    return driver


def save_cookies(driver):
    with open("cookies.json", "w") as file:
        import json
        json.dump(driver.get_cookies(), file)

def load_cookies(driver):
    if os.path.exists("cookies.json") and os.path.getsize("cookies.json") > 0:
        with open("cookies.json", "r") as file:
            import json
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print("Куки завантажено успішно!")
        return driver
    else:
        return driver
        print("Файл 'cookies.json' не існує або порожній. Виконується новий логін...")

def poshmark_registration(driver):
    driver.get("https://poshmark.com/signup") 
    time.sleep(random.uniform(2, 5))
    driver.find_element(By.ID, "firstName").send_keys("Romani") 
    time.sleep(random.uniform(2, 5))
    driver.find_element(By.ID, "lastName").send_keys("Koelon")   
    time.sleep(random.uniform(2, 5))
    driver.find_element(By.ID, "email").send_keys("Koelon_Romani_1974@gmail.com")  
    time.sleep(random.uniform(2, 5))
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys("Romani_1974")  
    time.sleep(random.uniform(2, 5))
    driver.find_element(By.ID, "password").send_keys("SecurePassword123!") 
    time.sleep(random.uniform(2, 5))

    gender_dropdown = driver.find_element(By.XPATH, "//div[@data-test='dropdown' and @name='gender']")
    gender_dropdown.click()
    time.sleep(random.uniform(2, 5))
    gender_option = driver.find_element(By.XPATH, "//li[@class='dropdown__menu__item']//div[contains(text(),'Male')]")
    gender_option.click() 

    country_dropdown = driver.find_element(By.XPATH, "//div[@data-test='dropdown' and @name='country']")
    country_dropdown.click()  
    time.sleep(random.uniform(2, 5))
    country_option = driver.find_element(By.XPATH, "//li[@class='dropdown__menu__item']//div[contains(text(),'Canada')]")
    country_option.click()

    next_button = driver.find_element(By.XPATH, "//button[@data-et-name='create_account']")
    next_button.click()

def login(driver, username = 'Romani_1974', password = 'SecurePassword123!'):
 
    driver.get("https://poshmark.com/login")   

    wait = WebDriverWait(driver, 10)
    try:
        username_field = wait.until(EC.presence_of_element_located((By.ID, "login_form_username_email")))
        password_field = wait.until(EC.presence_of_element_located((By.ID, "login_form_password")))
        
        username_field.clear()
        username_field.send_keys(username)
        
        password_field.clear()
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'][data-pa-name='login']")
        login_button.click()
    except:
        pass


    time.sleep(30)




    
def create_create_listing(driver, data):
    driver.get('https://poshmark.com/create-listing')
    wait = WebDriverWait(driver, 15)

    wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(),'Create Listing')]")))
    
    title_field = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//input[@placeholder='What are you selling? (required)']")))
    title_field.clear()
    title_field.send_keys(data['title'])
    

    description_field = driver.find_element(By.XPATH, "//textarea[@placeholder='Describe it! (required)']")
    description_field.clear()
    description_field.send_keys(data['description'])
    

    try:
        price_field = driver.find_element(By.ID, "price")
        price_field.clear()
        price_field.send_keys(data['price'])
    except Exception as e:
        print(e)
    

    try:
        brand_field = driver.find_element(By.ID, "brand")
        brand_field.clear()
        brand_field.send_keys(data['brand'])
    except Exception as e:
        print(e)
    
    try:
        category_dropdown = driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'listing-editor__category-container')]//div[contains(@class, 'dropdown__selector')]"
        )
        category_dropdown.click()
        category_option = wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//ul/li/a/div/p[normalize-space(text())='{data['category']}']")))
        category_option.click()
    except Exception as e:
        print(e)
    

    try:
        single_button = driver.find_element(
            By.XPATH, "//button[contains(text(),'Single Item')]")
        single_button.click()
    except Exception as e:
        print(e)
    
    time.sleep(200) 

def main():
    driver = init_web_driver_with_auth(0)

    try:
        driver.get('https://poshmark.com')
        driver = load_cookies(driver)
        driver.refresh()  
    except FileNotFoundError as e:
        print(e)
    
    
    # poshmark_registration(driver)
    login(driver)
    create_create_listing(driver, data)
    time.sleep(600)

    save_cookies(driver)

    return 
       

if __name__ == '__main__':
    # driver = init_web_driver_with_auth(3)
    # driver.get("https://2ip.ua/")
    main()
    time.sleep(random.uniform(2, 5))
    # main()
