import asyncio
import inspect
import json
from logging import Logger
from PIL import Image, ImageOps
import io
import os
from enum import Enum
from typing import Literal
import aiofiles
import aiohttp
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from local_db.crud import create_user, get_user_by_name
from local_db.models import Product, User
from poshmark.logger import Loger
from accounts_api.connector import APIConnector
import time
import requests


def get_user_agents():
    with open(os.path.join(os.getcwd(), 'user_agents.json'), 'r') as f:
        user_agents = json.load(f)
    return user_agents


def normal_time(epoche):
    if epoche > 60:
        minutes = int(epoche // 60)
        seconds = int(epoche % 60)
    else:
        minutes = 0
        seconds = int(epoche)
    return f'{minutes} минут, {seconds} секунд'


class ErrorType(Enum):
    NoError = -1
    BanError = 1
    CancelPost = 2
    RepostError = 3
    WhileFillError = 4


class BrowserManager:
    load_page = 3.0
    def __init__(
            self,
            headless=False,
            slow_mo=50, proxy_port=None,
            UA_browser: Literal['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera'] = 'Firefox',
            UA_system: Literal['Windows', 'Mac', 'Linux'] = 'Linux',
            UA_numb: int = 0, *,
            test_mode=False,
            proxy_check: str = None,
            safety_factor: float = 1.5
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser: Browser = None
        self.playwright: Playwright = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.semaphore = asyncio.Semaphore(1)
        self._uploadede_uniq_photo = set()
        self._cookie_path = ''
        self.count = 0
        self._requests = []  #TODO FIX
        if not proxy_port:
            self.proxy = None
        else:
            self.proxy = {'server': f'http://localhost:{proxy_port}'}
        user_ag = get_user_agents()
        self.user_agent = user_ag[UA_system][UA_browser][UA_numb]
        self.user: User = None
        self._last_error_type: ErrorType = ErrorType.NoError
        self._error_processed = True
        loger = Loger('poshmark', __name__)
        self.log: Logger = loger.get_logger
        self.test_mode = test_mode
        self.accounts_api = APIConnector(base_url="http://fastapi_app:8093")
        self.proxy_check = proxy_check
        self.spead_proxy = None
        if self.spead_proxy is not None:
            self.timeout_load = (self.load_page + self.spead_proxy) * safety_factor
            self.timeout_user = self.spead_proxy * safety_factor
        else:
            self.timeout_load = 10
            self.timeout_user = 1

    @property
    def last_error(self):
        return self._last_error_type

    @last_error.setter
    def last_error(self, value: ErrorType):
        self._last_error_type = value
        self._error_processed = False

    def __test_proxy(self):
        if self.proxy_check is not None:
            proxy_url = self.proxy_check.split('/'[-1])
            test_url = "https://www.google.com"
            proxies = {
                'http': f'socks5://{proxy_url}',
                'https': f'socks5://{proxy_url}'
            }

            start_time = time.time()

            try:
                response = requests.get(test_url, proxies=proxies, timeout=10)
                response.raise_for_status()
                latency = time.time() - start_time
                formatted_latency = f"{latency:.2f}"
                self.spead_proxy = float(formatted_latency)
            except requests.exceptions.RequestException as e:
                self.spead_proxy = None

    async def start_browser(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            proxy=self.proxy,

        )
        download_path = os.path.join(os.getcwd(), 'downloads')
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        self.context = await self.browser.new_context(
            viewport={'width': 1500, 'height': 700},
            **self.user_agent,
            timezone_id='America/New_York',
            bypass_csp=True,
            ignore_https_errors=True,
            color_scheme='dark',
            extra_http_headers={
                'accept-language': 'en-US,en;q=0.9',
                'upgrade-insecure-requests': '1',

            },

            accept_downloads=True
        )
        self.page = await self.context.new_page()
        # self.page.on('download', lambda download: download.save_as(os.path.join(download_path, download.suggested_filename)))
        self.context.on('request', self._request_listener)
        self.log.info('Start browser')

    def get_account_name_from_cookies(self, cookies):
        for cookie in cookies:
            if cookie.get('name') == 'ui' and cookie.get('domain') == "poshmark.com":
                data = cookie.get('value')
                if not data:
                    continue
                name = data.split('%22%2C%22uid')[0].split('A%22')[-1]
                if not name:
                    continue
                return name
        return None

    async def save_cookies(self, *, new_name=None) -> None:
        """Save cookies to a file."""
        # if user_id:
        #     self.accounts_api.update_user_cookies(user_id, await self.page.context.cookies())
        if new_name:
            path = os.path.join(os.getcwd(), new_name)
        else:
            path = self._cookie_path
        if not path:
            path = os.path.join(os.getcwd(), 'kyyka.json')
        cookies = await self.page.context.cookies()
        print(f'resave cookies to {self._cookie_path}')
        with open(path, 'w') as f:
            json.dump(cookies, f)

    def load_user_from_cookies(self, *, path=None, cookies_=None) -> User:
        if path:
            with open(path, 'r') as f:
                data = json.load(f)
                cookies = data['cookies'] if 'cookies' in data else data
        elif cookies_:
            cookies = cookies_
        else:
            raise Exception('Need path or cookies_ arguments')

        account_name = self.get_account_name_from_cookies(cookies)
        user = get_user_by_name(account_name)
        if not user:
            user = create_user(account_name, cookies)
        self.user = user
        self.log.debug('Cookies loaded')
        self.log.info(f'Loaded user[{user.name}, id:{user.id}]')

    async def load_cookies(self, path: str) -> None:
        """Load cookies from a file."""

        self._cookie_path = path
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                cookies = data['cookies'] if 'cookies' in data else data
                for kyka in cookies:
                    kyka['sameSite'] = 'None'
                await self.context.add_cookies(cookies)
                self.load_user_from_cookies(cookies_=cookies)

        except FileNotFoundError:
            print("Cookie file not found, starting with a clean session.")

    async def _request_listener(self, request):
        try:
            self._requests.append(request.url)
        except:
            pass

    async def goto_page(self, url: str, *, referer: str = None, timeout: int = 300000):
        await self.page.goto(url, timeout=timeout, wait_until='load')

    async def download_image(self, url, dest):

        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(dest, mode='wb') as f:
                            image_data = await response.read()
                            temp_image_path = dest + "_temp"
                            with open(temp_image_path, 'wb') as temp_file:
                                temp_file.write(image_data)

                            # Создаем квадратное изображение с отражением
                            center_image_on_square_canvas(temp_image_path, dest)

                            # Удаляем временный файл
                            os.remove(temp_image_path)
                        # print(f'Download file[{dest}] from url[{url}]')
                    else:
                        self.log.error(f"Failed to download {url}: Status code {response.status}")
        except Exception as e:
            self.log.exception(f"Error occurred while downloading {url}: {e}")

    async def close_browser(self):
        try:
            await self.browser.close()
        except:
            pass

        try:
            await self.playwright.stop()
        except:
            pass

    async def run(self, url: str, cookies_path: str):
        await self.start_browser()
        await self.load_cookies(cookies_path)
        await self.goto_page(url)


def create_square_with_reflection(image_path, output_path):
    """
   Функция для создания квадратного изображения с зеркальным отражением краев.

   :param image_path: Путь к исходному изображению.
   :param output_path: Путь для сохранения квадратного изображения.
   """
    with Image.open(image_path) as img:
        # Получаем размеры изображения
        width, height = img.size

        # Определяем размер новой квадратной стороны
        new_size = max(width, height)

        # Создаем новое квадратное изображение
        new_image = Image.new("RGB", (new_size, new_size))

        # Вставляем исходное изображение по центру
        if width > height:
            # Добавляем зеркальные отражения сверху и снизу
            offset = (new_size - height) // 2
            new_image.paste(img, (0, offset))

            # Создаем отраженные верхние и нижние части
            top_reflection = img.crop((0, 0, width, offset))
            bottom_reflection = img.crop((0, height - offset, width, height))
            new_image.paste(ImageOps.flip(top_reflection), (0, 0))
            new_image.paste(ImageOps.flip(bottom_reflection), (0, new_size - offset))

        else:
            # Добавляем зеркальные отражения слева и справа
            offset = (new_size - width) // 2
            new_image.paste(img, (offset, 0))

            # Создаем отраженные левые и правые части
            left_reflection = img.crop((0, 0, offset, height))
            right_reflection = img.crop((width - offset, 0, width, height))
            new_image.paste(ImageOps.mirror(left_reflection), (0, 0))
            new_image.paste(ImageOps.mirror(right_reflection), (new_size - offset, 0))

        # Сохраняем новое изображение
        new_image.save(output_path)


def center_image_on_square_canvas(input_path, output_path, padding=100, canvas_color=(255, 255, 255)):
    """
    Функция для центрирования изображения на квадратном полотне с полями со всех сторон.

    :param input_path: Путь к исходному изображению.
    :param output_path: Путь для сохранения квадратного изображения.
    :param canvas_color: Цвет полотна (по умолчанию прозрачный).
    """
    with Image.open(input_path) as img:
        # Получаем размеры изображения
        width, height = img.size

        # Определяем размер новой квадратной стороны, добавляя паддинги
        new_size = max(width, height) + 2 * padding

        # Определяем режим изображения (RGBA или RGB в зависимости от canvas_color)
        mode = 'RGBA' if len(canvas_color) == 4 else 'RGB'

        # Создаем новое квадратное изображение с заданным цветом фона
        new_image = Image.new(mode, (new_size, new_size), canvas_color)

        # Рассчитываем смещения для центрирования изображения на квадратном полотне
        offset_x = (new_size - width) // 2
        offset_y = (new_size - height) // 2

        # Вставляем исходное изображение по центру
        # Проверяем, нужно ли использовать альфа-канал
        if mode == 'RGBA' and img.mode in ('RGBA', 'LA'):
            # Вставляем изображение с маской альфа-канала
            new_image.paste(img, (offset_x, offset_y), img)
        else:
            # Вставляем изображение без альфа-канала
            new_image.paste(img, (offset_x, offset_y))

        # Сохраняем новое изображение
        new_image.save(output_path)
