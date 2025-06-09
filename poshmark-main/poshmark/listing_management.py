from ._browser_manager import BrowserManager
from typing import List, Dict, Literal
from .logger import Loger
import asyncio
import inspect
import traceback
from random import randint
from accounts_api.connector import APIConnector

class PoshmarkProductManager(BrowserManager):
    def __init__(self, headless=False, slow_mo=50, proxy_port=None, UA_browser: Literal['Chrome'] | Literal['Firefox'] | Literal['Safari'] | Literal['Edge'] | Literal['Opera'] = 'Firefox', UA_system: Literal['Windows'] | Literal['Mac'] | Literal['Linux'] = 'Linux', UA_numb: int = 0, *, test_mode=False):
        super().__init__(headless, slow_mo, proxy_port, UA_browser, UA_system, UA_numb, test_mode=test_mode)
        self._responses = []
        self._string_for_collect = ''
        self.accounts_api = APIConnector(base_url="http://fastapi_app:8093")

    async def get_list_products_sku(self, sku):
        """
        Получить список продуктов по SKU.
        """
        try:
            products = self.accounts_api.get_products_by_sku(sku)
            return products
        except Exception as e:
            self.log.exception(f"Error fetching products by SKU {sku}: {str(e)}")
            return []

    async def get_accounts_info(self, user_ids: List[int]):
        """
        Получить информацию об аккаунтах по списку user_id.
        """
        accounts_info = {}
        for user_id in user_ids:
            try:
                account_info = self.accounts_api.get_user_by_id(user_id)
                if account_info:
                    accounts_info[user_id] = account_info
            except Exception as e:
                self.log.exception(f"Error fetching account info for user_id {user_id}: {str(e)}")
        return accounts_info

    async def gather_data(self, sku):
        """
        Собрать данные о продуктах и аккаунтах.
        """
        # Шаг 1: Получаем список продуктов по SKU
        products = await self.get_list_products_sku(sku)

        if not products:
            self.log.exception("No products found for the given SKU.")
            return {}

        # Шаг 2: Извлекаем уникальные user_id из продуктов
        user_ids = list(set([product['user_id'] for product in products if product['user_id'] == 9]))

        # Шаг 3: Получаем информацию об аккаунтах по user_id
        accounts_info = await self.get_accounts_info(user_ids)

        # Шаг 4: Составляем словарь данных
        data = {}
        for product in products:
            if product['status'] == 'WITHDRAWN':
                continue
            user_id = product['user_id']
            if user_id not in data:
                data[user_id] = {
                    'account_info': accounts_info.get(user_id),
                    'products': []
                }
            data[user_id]['products'].append(product)

        return data
    
    async def __save_item(self):
        await self.page.locator('[data-et-name="update"]').click()
        await asyncio.sleep(randint(10,15))
        await self.page.locator('[data-et-name="list"]').click()
        await asyncio.sleep(randint(10,15))

    async def change_origin_price(self, url, new_origin_price):
        try:

            await self.goto_page(url, referer=f'https://poshmark.com/closet/{self.user.name}')
            
            await self.page.locator('input[data-vv-name="originalPrice"]').fill(str(int(new_origin_price)))
            await asyncio.sleep(randint(5, 12))
            
            await self.__save_item()
            await asyncio.sleep(randint(5, 12))
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def change_prices_with_ratio(self, url, new_listing_price):
        try:

            await self.goto_page(url, referer=f'https://poshmark.com/closet/{self.user.name}')
            origin_price_input = self.page.locator('input[data-vv-name="originalPrice"]')
            origin_price_value = await origin_price_input.input_value()
            old_original_price = float(origin_price_value)  # Преобразование строки в число

            # Извлечение цены листинга из input элемента (пример: 'input[name="listing_price"]')
            listing_price_input = self.page.locator('input[data-vv-name="listingPrice"]')
            listing_price_value = await listing_price_input.input_value()
            old_listing_price = float(listing_price_value)
            # Вычисление текущей пропорции между listing price и origin price
            price_ratio = old_listing_price / old_original_price if old_original_price != 0 else 1
            new_origin_price = new_listing_price / price_ratio
            await origin_price_input.fill(str(int(new_origin_price)))
            await asyncio.sleep(randint(5, 12))
            
            await listing_price_input.fill(str(int(new_listing_price)))
            await asyncio.sleep(randint(5, 12))
            await self.__save_item()
            await asyncio.sleep(randint(5, 12))
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def delete_listing(self, url):
        try:

            await self.goto_page(url)
            await self.page.locator('[data-et-name="delete"]').click()
            await asyncio.sleep(randint(10,15))
            button_yes_locator = self.page.locator('div[data-test="modal-footer"] button.btn--primary').nth(2)
            await button_yes_locator.click()
            await asyncio.sleep(randint(10,15))
            await asyncio.sleep(10)
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def add_size(self, url, new_size):
        try:
            await self.goto_page(url)
            drop_down = self.page.locator('[selectortestlocator="size"]')

            # Открываем выпадающий список размеров, если он не открыт
            expanded_state = await drop_down.get_attribute('expandedoveridestate')
            if not expanded_state or expanded_state.lower() != 'true':
                await self.page.locator('[data-test="size"]').click()
                await asyncio.sleep(2)

            # Получаем все кнопки размеров
            size_buttons = await drop_down.locator('li button').all()

            # Перебираем размеры, которые хотим добавить
            for size in new_size:
                size_found = False
                for button in size_buttons:
                    button_text = await button.text_content()
                    if button_text.strip().lower() == size.lower():
                        await button.click()
                        size_found = True
                        break
                
                if not size_found:
                    print(f"Size '{size}' not found in the dropdown")

            # Кликаем по кнопке 'Done' после выбора размеров
            done_button = drop_down.get_by_role('button', name='Done')
            if await done_button.is_visible():
                await done_button.click()
                await self.__save_item()
                await asyncio.sleep(randint(5, 12))
            else:
                print("Done button not found or not visible")
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)


