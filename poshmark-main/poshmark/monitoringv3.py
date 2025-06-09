from ast import List
import asyncio
from collections import defaultdict
from http.client import responses
import inspect
from random import randint, random
import re
from socket import timeout
import traceback
from urllib import response
import requests
import json
import os
import base64
from os.path import join as os_join
from jsonpath_ng import jsonpath, parse
from typing import List, Dict, Literal
from api.api import API
from api.dto import ProductDTO
from config import Config
from poshmark._browser_manager import BrowserManager
from poshmark.gather_validate_address import gather_and_validate_adrress
from local_db.crud import get_product_by_user, get_products_by_ids, get_user_by_name
from local_db.models import Product
from playwright.async_api import Request, Response
from poshmark.logger import Loger
from datetime import datetime
import math


def get_dict(data, target_key):
    # Если это список, рекурсивно обрабатываем каждый элемент списка
    if isinstance(data, list):
        for item in data:
            result = get_dict(item, target_key)
            if result is not None:
                return result

    # Если это словарь, рекурсивно обрабатываем каждый ключ
    elif isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                return value
            result = get_dict(value, target_key)
            if result is not None:
                return result

    # Если это другой тип данных, просто возвращаем None
    return None


def parse_items(data: list[dict]) -> dict[str, dict]:
    items_dict = {}
    for item in data:
        itm_dict = {
            'id': item.get('id'),
            'status': 'not_for_sale',
            'original_price_amount': float(item.get('original_price_amount', {}).get('val', 0)),
            'price_amount': float(item.get('price_amount', {}).get('val', 0)),
            'colors': [],
            'multi_item': False,

        }
        inventory = item['inventory']
        if (status := inventory.get('status')):
            itm_dict['status'] = status
        if (colors := item.get('colors')):
            color_names = [col.get('name', '').lower() for col in colors]
            itm_dict['colors'] = color_names
        if inventory['multi_item']:
            itm_dict['multi_item'] = True
            # available_sizes = []
            all_sizes = []
            for size in inventory.get('size_quantities', []):
                item_size = size['size_id']
                all_sizes.append(item_size)
                # if size.get('status') == 'available':
                #     available_sizes.append()

            itm_dict['sizes'] = all_sizes
            # itm_dict['available_sizes'] = available_sizes

        else:
            if inventory['size_quantities']:
                size = inventory['size_quantities'][0]
                itm_dict['sizes'] = [size.get('size_id')]

        if itm_dict['id'] in items_dict:
            print(f'error{itm_dict["id"]}')
        else:
            items_dict[itm_dict['id']] = itm_dict
    return items_dict


def get_info_by_api(user_name: str, max_id: int):
    api_url = f"https://poshmark.com/vm-rest/users/{user_name}/posts/filtered"
    params = {
        "request": json.dumps({
            "filters": {
                "department": "All",
                "inventory_status": ["all"]
            },
            "experience": "all",
            "max_id": max_id,
            #
            "count": 20
        }),
        "summarize": "true",
        "app_version": "2.55",
        "pm_version": "2024.29.0"
    }
    return requests.get(url=api_url, params=params).json()


def get_all_data(closet_url: str):
    resp = requests.get(closet_url)
    user_name = closet_url.split('/')[-1]
    start_json = 'window.__INITIAL_STATE__='
    end_json = ';(function(){'
    initial_json = json.loads(resp.text.split(start_json)[-1].split(end_json)[0])
    listed_count = resp.text.split('<span data-test="closet_listings_count">')[-1].split('</span>')[0]
    try:
        listed_count = int(listed_count.strip())
    except:
        return
    jsonpath_expr = parse(f'$..listingsPostData')
    matches = jsonpath_expr.find(initial_json)
    if matches:
        first_data = matches[0].value

    listing_items = first_data['data']
    # items = parse_items(listing_data)
    has_next = 'more' in first_data
    if has_next:
        next_max_id = first_data['more'].get('next_max_id')
        while len(listing_items) < listed_count and has_next:
            next_json = get_info_by_api(user_name, next_max_id)
            listing_items += next_json['data']
            if 'more' in next_json:
                next_max_id = next_json['more'].get('next_max_id')
            else:
                break

    return listing_items


def create_product_dto_mapping(products: List[Product], product_dtos: List[ProductDTO]) -> Dict[str, ProductDTO]:
    dto_mapping = {(dto.id, dto.variant_color): dto for dto in product_dtos}

    result_mapping = {}
    for product in products:
        key = (product.api_id, product.variant_color)
        if key in dto_mapping:
            result_mapping[product.id_in_shop] = dto_mapping[key]

    return result_mapping


class PoshmarkMonitoring(BrowserManager):
    def __init__(self, headless=False, slow_mo=50, proxy_port=None,
                 UA_browser: Literal['Chrome'] | Literal['Firefox'] | Literal['Safari'] | Literal['Edge'] | Literal[
                     'Opera'] = 'Firefox', UA_system: Literal['Windows'] | Literal['Mac'] | Literal['Linux'] = 'Linux',
                 UA_numb: int = 0, *, test_mode=False, safety_factor=None):
        super().__init__(headless, slow_mo, proxy_port, UA_browser, UA_system, UA_numb, test_mode=test_mode)
        self._responses = []
        self._string_for_collect = ''
        loger = Loger('poshmark-offers', __name__)

    async def delete_listing(self, url):
        try:

            await self.goto_page(url)
            await self.page.locator('[data-et-name="delete"]').click()
            await asyncio.sleep(randint(10, 15))
            # button_yes_locator = self.page.locator('div[data-test="modal-footer"] button.btn--primary')#.nth(2)
            # await button_yes_locator.click()
            modal_elements = self.page.locator('div[data-test="modal-container"]')
            for i in range(await modal_elements.count()):
                modal = modal_elements.nth(i)
                if await modal.is_visible():
                    # Выбрать и кликнуть по кнопке "Yes" в модальном окне
                    button_yes_locator = self.page.locator('div[data-test="modal-footer"] button.btn--primary').filter(
                        has_text="Yes")
                    await button_yes_locator.click()
            await asyncio.sleep(randint(10, 15))
            await asyncio.sleep(10)
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0])
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def __get_listed_items_from_api(self, products: list[Product]) -> list[ProductDTO]:
        api = API(Config.API_URL, Config.API_TOKEN)
        api_items = []
        ids = set([product.api_id for product in products])
        for item_id in ids:
            api_items += await api.product.get_product(item_id)

        return api_items

    async def __change_available_size(self, size_dict: dict):
        '''изменяет доступные размеры товара'''
        sold = size_dict['sold_size']
        available = size_dict['api_size']

        sol_availavle_lsit = sold + available
        drop_down = self.page.locator('[selectortestlocator="size"]')

        table_rows = (await self.page.locator('.listing-editor__inventory-table').locator('tr').all())[1:]
        dict_of_elements = {}

        for tr in table_rows:
            dict_of_elements[(await tr.locator('[class="va--m p--l--5 p--r--5"]').text_content()).strip()] = tr

        for size in sol_availavle_lsit:
            if not size in dict_of_elements:
                continue
            if size in sold:
                await dict_of_elements[size].get_by_placeholder('Quantity').fill('0')
            if size in available:
                await dict_of_elements[size].get_by_placeholder('Quantity').fill('1')

    async def __get_poshmark_size_dict(self):
        drop_down = self.page.locator('[selectortestlocator="size"]')
        if not await drop_down.get_attribute('expandedoveridestate'):
            await self.page.locator('[data-test="size"]').click()
            await asyncio.sleep(2)
        lis = await drop_down.locator('.p--3').locator('li').all()
        names = list(map(lambda x: x.strip().lower(), await asyncio.gather(*[elem.text_content() for elem in lis])))

        sizes_dict = dict(zip(names, lis))
        return names, sizes_dict

    async def __add_available_size(self, sizes: set):
        drop_down = self.page.locator('[selectortestlocator="size"]')
        names, sizes_dict = self.__get_poshmark_size_dict()
        poshmark_size = set(names).intersection(sizes)
        dif = set(sizes).difference(poshmark_size)
        if dif:
            print(f'invalid sizes:{dif}')
        for inter in poshmark_size:
            await sizes_dict[inter].click()
            await asyncio.sleep(1)
        await drop_down.get_by_role('button', name='Done').click()
        return

    async def __save_item(self):
        await self.page.locator('[data-et-name="update"]').click()
        await asyncio.sleep(randint(10, 15))
        await self.page.locator('[data-et-name="list"]').click()
        await asyncio.sleep(randint(10, 15))
        await self.page.wait_for_load_state('load')

    async def change_item(self, data: dict):
        self.goto_page(data['url'], referer=f'https://poshmark.com/closet/{self.user.name}')

        if data['sold_size']:
            await self.__change_available_size(data)

        if data['add_size']:
            await self.__add_available_size(data['add_size'])

        await self.__save_item()
        await asyncio.sleep(randint(10, 15))

    def _viewing_items(
            self,
            site_item: dict,
            api_item: ProductDTO,
            url: str
    ) -> tuple[bool, dict]:
        site_size = site_item['sizes']
        api_size = api_item.post_sizes

        sold = [item for item in site_size if item not in api_size]

        add_size = [item for item in api_size if item not in site_size]

        if any([sold, add_size]):
            return {
                'need': True,
                'sold_size': sold,
                'add_size': add_size,
                'api_item': api_item,
                'api_size': api_size,
                'url': url
            }

        return {'need': False, }

    def _chech_for_change(
            self,
            listed_mapping: dict[str, Product],
            api_mapping: dict[str, ProductDTO],
            items_from_site: dict[str, list]
    ):
        to_change_dict = {}
        for listed_item_key in listed_mapping.keys():
            api_item = api_mapping.get(listed_item_key)
            itm_from_site = items_from_site.get(listed_item_key)
            listed_itm = listed_mapping[listed_item_key]
            if not itm_from_site or not api_item:
                continue
                # TODO ADD CALLBACK TO API
            change = self._viewing_items(itm_from_site, api_item, listed_itm.edit_url)
            if change['need']:
                to_change_dict[listed_item_key] = change
        ...
        return to_change_dict

    def get_items_from_site(self):
        return parse_items(get_all_data(f'https://poshmark.com/closet/{self.user.name}'))

    async def monitoring_items(self, *, items_by_id: list[str] = None, items_by_user_name: str = None) -> dict[
        str, dict]:
        if items_by_id:
            listed_items = get_products_by_ids(items_by_id)
        elif items_by_user_name:
            listed_items = get_product_by_user(get_user_by_name(items_by_user_name))
        else:
            raise ValueError('You must provide either items_by_id or items_by_user_name')
        listed_mapping = {item.id_in_shop: item for item in listed_items}
        api_items = await self.__get_listed_items_from_api(listed_items)
        api_mapping = create_product_dto_mapping(listed_items, api_items)
        items_from_site = parse_items(get_all_data(f'https://poshmark.com/closet/{self.user.name}'))

        to_change_dict = await self._chech_for_change(listed_mapping, api_mapping, items_from_site)
        return to_change_dict

    async def _change_price(self, url, new_op: int = None, new_lp: int = None):
        try:

            await self.goto_page(url, referer=f'https://poshmark.com/closet/{self.user.name}')
            if new_op:
                await self.page.locator('input[data-vv-name="originalPrice"]').fill(str(int(new_op)))
                await asyncio.sleep(randint(5, 12))
            if new_lp:
                await self.page.locator('input[data-vv-name="listingPrice"]').fill(str(int(new_lp)))
                await asyncio.sleep(randint(5, 12))
            await self.__save_item()
            await asyncio.sleep(randint(10, 15))
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0])
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def change_availability(self, url):
        try:

            await self.goto_page(url, referer=f'https://poshmark.com/closet/{self.user.name}')

            ava_div = self.page.locator('[data-et-name="listingEditorAvailabilitySection"]')
            await ava_div.locator('[items="available,not_for_sale,coming_soon"]').click()
            await asyncio.sleep(2.1)
            await self.page.locator('a[data-et-name="not_for_sale"]').click()

            await asyncio.sleep(randint(5, 12))

            await self.__save_item()
            await asyncio.sleep(randint(5, 12))
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback, limit=3))
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0])
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def uppdate_price(self, items: List[Product], OAP: int, LAP: int):
        """Update price for OAP, LAP percentage of current

        Args:
            items (List[Product]): List of listed products  
            OAP (int): Original additional percent - the percent by which the price increases
            LAP (int): Listing additional percent - the percent by which the price increases
        """
        orig_milti = (1 + (OAP / 100))
        listing_milti = (1 + (LAP / 100))

        items_from_site = self.get_items_from_site()
        for item in items:
            item_id = item.id_in_shop
            site_item = items_from_site.get(item_id)
            if not site_item:
                print(f'Item [{item_id}] dosen`t exist on marketplace')
                continue
            old_origin_price = site_item['original_price_amount']
            old_listing_price = site_item['price_amount']

            new_op = old_origin_price * orig_milti
            new_lp = old_listing_price * listing_milti
            await self._change_price(item.edit_url, int(new_op), int(new_lp))

    async def _gather_information_item(self, url):
        try:

            await self.goto_page(url, referer=f'https://poshmark.com/closet/{self.user.name}')
            item = {}
            # Извлечение item_id из URL
            item_id = url.split('/')[-1]
            item['item_id'] = item_id
            item['item_url'] = url

            # Извлечение значения SKU из input элемента
            sku_input = self.page.locator('input[data-vv-name="sku"]')
            sku_value = await sku_input.input_value()
            item['sku'] = sku_value

            # Извлечение заголовка товара из input элемента (пример: 'input[name="title"]')
            title_input = self.page.get_by_placeholder("What are you selling? (required)")
            title_value = await title_input.input_value()
            item['title'] = title_value

            # Извлечение оригинальной цены из input элемента (пример: 'input[name="origin_price"]')
            origin_price_input = self.page.locator('input[data-vv-name="originalPrice"]')
            origin_price_value = await origin_price_input.input_value()
            item['original_site_price'] = float(origin_price_value)  # Преобразование строки в число

            # Извлечение цены листинга из input элемента (пример: 'input[name="listing_price"]')
            listing_price_input = self.page.locator('input[data-vv-name="listingPrice"]')
            listing_price_value = await listing_price_input.input_value()
            item['listing_price'] = float(listing_price_value)  # Преобразование строки в число

            # Извлечение статуса товара из input элемента (пример: 'input[name="status"]')
            status_span = self.page.locator(
                'div[data-et-name="listingEditorAvailabilitySection"] div[data-test="dropdown"] span')
            status_value = await status_span.text_content()
            item['status'] = status_value.strip()
            colors = []
            color_items = self.page.locator('div[data-et-name="color"] ul li span:nth-of-type(2)')
            for color_span in await color_items.all():
                color_text = await color_span.text_content()
                colors.append(color_text.strip())

            sizes = []
            size_cells = self.page.locator('table.listing-editor__inventory-table tbody tr td:first-child')
            for size_cell in await size_cells.all():
                size_text = await size_cell.text_content()
                sizes.append(size_text.strip())

            item["multi_item"] = 'True'
            item["variants"] = []

            if len(colors) == 0:
                colors = [None]  # Если нет цветов, передаем пустой список

            if len(sizes) == 0:
                sizes = [None]  # Если нет размеров, передаем пустой список

                # Генерируем варианты для каждого цвета и размера
            for color in colors:
                for size in sizes:
                    variant_dict = {
                        "price_adjustment": 0,
                        "quantity": "",
                    }
                    if color:
                        variant_dict['color'] = color
                    if size:
                        variant_dict['size'] = size
                    item['variants'].append(variant_dict)
            return item

        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0])
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def random_discount(self, count, discount_size):
        """Drop listing price of few random items by discount_size
        Example:
            price_before = 200
            drop amount = 1 - (discount_size / 100)
            if discount_size = 20
            drop amount = 0.8
            price_after = 160
        """
        items_from_site = self.get_items_from_site()
        random_selection = random.sample(list(items_from_site.keys()), count)
        for item_id in random_selection:
            url = f'https://poshmark.com/edit-listing/{item_id}'
            item = items_from_site[item_id]
            item_listing_price = item['price_amount']
            drop_amount = 1 - (discount_size / 100)
            new_price = int(item_listing_price * drop_amount)
            await self._change_price(url, new_lp=new_price)

    async def _response_collector(self, response: Response):
        try:
            request_url = response.request.url
            if self._string_for_collect in request_url:
                response_body = await response.json()
                self._responses.append(response_body)
        except Exception as e:
            print(f"Failed to collect response for {request_url}: {e}")

    async def __get_offer_links(self, data_dict: dict):
        """Извлекает ссылки на детализированные страницы офферов."""
        try:
            info_about_offers = data_dict['data'][1]
            offers_list: list = info_about_offers['content']['data']
            offer_links = []

            for item in offers_list:
                target_url = item['target']['url']
                offer_links.append(f'https://poshmark.com{target_url}')

            return offer_links
        except Exception as e:
            print(f"Not offers")
            return []

    async def _try_get_all_offer_links(self):
        cur_responses = self._responses.copy()
        offer_links = []
        for req in cur_responses:
            offer_links.extend(await self.__get_offer_links(req))
        return offer_links

    async def check_offers(self, user_id):
        """Check offers on marketplace"""
        self._string_for_collect = '/offers/feed?pm_version'
        self._responses.clear()
        self.context.on('response', self._response_collector)
        await self.goto_page('https://poshmark.com/offers/my_offers', referer='https://poshmark.com/feed',
                             timeout=300000)
        await self.page.wait_for_load_state('load', timeout=450000)
        # Шаг 1: Сбор ссылок на детализированные страницы офферов
        offer_links = await self._try_get_all_offer_links()
        detailed_offers = []

        # Шаг 2: Переход по ссылкам и сбор детализированных данных
        for offer_url in offer_links:
            try:

                # Переходим по каждой ссылке и перехватываем респонсы
                detailed_offer_data = await self._get_detailed_offer_data(offer_url)

                if detailed_offer_data:
                    detailed_offers.append(detailed_offer_data)
                    # Шаг 3: Обработка каждого детализированного оффера
                    for offer in detailed_offer_data:
                        offer['user_id'] = user_id
                        offer_url_messages = offer['offer_url']
                        # listing_info = offer.get('listings_info', [{}])[0]
                        # listing_price = listing_info.get('price_amount', {}).get('val')

                        await self.process_offer(offer_url_messages, user_id)


            except Exception as e:
                print(f"Error processing offer for URL {offer_url}: {e}")
                continue

        # with open(os.path.join(os.getcwd(), 'offers_result2.json'), 'w') as f:
        #     json.dump(detailed_offers, f, indent=4)

        return detailed_offers

    async def _get_detailed_offer_data(self, offer_url):
        """Сбор детализированных данных по офферу."""
        try:
            # Очищаем респонсы перед переходом на новую страницу
            self._string_for_collect = 'offers/active'
            self._responses.clear()
            self.context.on('response', self._response_collector)

            # Переходим по ссылке
            await self.goto_page(offer_url, timeout=300000)
            await asyncio.sleep(5)
            if not self._responses:
                print(f"No responses received for URL: {offer_url}")
                return []
                # Обрабатываем респонсы, чтобы получить детализированные данные
            detailed_offers = []
            for response_data in self._responses:

                if 'data' not in response_data:
                    print(f"Key 'data' not found in response: {response_data}")
                    continue

                offers = self._extract_offer_details(response_data['data'])
                detailed_offers.extend(offers)

            return detailed_offers

            # return []

        except Exception as e:
            print(f"Error processing detailed offer data for URL {offer_url}: {e}")
            return None

    def _extract_offer_details(self, data):
        """Извлечение детализированных данных оффера из респонса."""

        offers = []

        for offer_data in data:
            print("=" * 50)
            print(offer_data)
            print("=" * 50)
            # Преобразование данных в нужные типы
            offer_amount = float(offer_data['latest_offer_message']['amount']['val']) if \
            offer_data['latest_offer_message']['amount']['val'] is not None else None
            listing_price = float(
                offer_data['listings_info'][0]['price_amount']['val']) if 'listings_info' in offer_data and offer_data[
                'listings_info'] and offer_data['listings_info'][0]['price_amount']['val'] is not None else None
            original_site_price = float(
                offer_data['listings_info'][0]['init_price_amount']['val']) if 'listings_info' in offer_data and \
                                                                               offer_data['listings_info'] and \
                                                                               offer_data['listings_info'][0][
                                                                                   'init_price_amount'][
                                                                                   'val'] is not None else None

            # Извлечение детализированных данных оффера
            offer_details = {
                'offer_id': offer_data['id'],
                'offer_url': f"https://poshmark.com/offers/{offer_data['id']}",
                'offer_amount': offer_amount,
                'listing_price': listing_price,
                'buyer_username': offer_data['buyer_info']['username'],
                'state': offer_data['state'],
                'status_message': offer_data['status_message'],
                'item_id': offer_data['listings_info'][0]['listing_id'] if 'listings_info' in offer_data and offer_data[
                    'listings_info'] else None,
                'item_title': offer_data['listings_info'][0]['title'] if 'listings_info' in offer_data and offer_data[
                    'listings_info'] else None,
                'item_url': offer_data['listings_info'][0]['product_url'] if 'listings_info' in offer_data and
                                                                             offer_data['listings_info'] else None,
                'original_site_price': original_site_price,
                'colors': [get_dict(offer_data, 'color')] if get_dict(offer_data, 'color') is not None else [],
                'sizes': [get_dict(offer_data, 'size')] if get_dict(offer_data, 'size') is not None else [],
                'status': offer_data['state'],
                'interaction_status': '',
                'user_id': 1
            }

            offers.append(offer_details)

        return offers

    async def process_offer(self, offer_url, user_id):
        try:
            # Перехват респонса для указанного URL
            self._string_for_collect = '/vm-rest/offers/'
            self._responses.clear()
            self.context.on('response', self._response_collector)

            # Переход по URL
            await self.goto_page(offer_url, timeout=300000)
            await asyncio.sleep(5)  # Даем время для завершения всех запросов

            # Обрабатываем перехваченные респонсы
            detailed_offer_data = None
            for response in self._responses:
                detailed_offer_data = self._extract_offer_messages(response['data'])

            if not detailed_offer_data:
                print(f"No detailed offer data found for URL: {offer_url}")
                return

            # Логика для работы с оффером
            if user_id == 2:
                await self.__insist_logik(detailed_offer_data)
            else:
                await self._process_offer_logic(detailed_offer_data)

        except Exception as e:
            print(f"Error processing offer at {offer_url}: {e}")

    def _extract_offer_messages(self, data):
        """Извлечение детализированных данных оффера из респонса."""
        offer_data = {
            'offer_id': data['id'],
            'listing_id': data['listing_ids'][0],
            'state': data['state'],
            'latest_offer': data['latest_offer_message'],
            'actions': data.get('actions', []),
            'buyer_info': data['buyer_info'],
            'seller_info': data['seller_info'],
            'offer_messages': data.get('offer_messages', []),
            'listings_info': data['listings_info']
        }
        return offer_data

    async def _process_offer_logic(self, detailed_offer_data):
        """Логика для обработки оффера."""
        offer_state = detailed_offer_data['state']
        latest_offer = detailed_offer_data['latest_offer']
        offer_messages = detailed_offer_data['offer_messages']

        # Рассчитываем минимальную цену, ниже которой будем отменять предложения
        listing_price = float(detailed_offer_data['listings_info'][0]['price_amount']['val'])
        threshold_price = math.ceil(listing_price * 0.9)
        if threshold_price % 10 == 0:
            threshold_price -= 1

        # Проверяем, отправляли ли мы уже контроффер
        first_counter_offer_price = None
        for offer in offer_messages:
            if offer['creator'] == 's':
                first_counter_offer_price = float(offer['amount']['val'])
                break

        seller_counter_offer_sent = first_counter_offer_price is not None
        print(first_counter_offer_price)

        if offer_state == 'sp' and latest_offer['creator'] == 'b' and not seller_counter_offer_sent:
            # listing_price = float(detailed_offer_data['latest_offer']['amount']['val'])
            # counter_offer_price = round(listing_price * 0.9, 2)
            await self._make_counter_offer(detailed_offer_data['offer_id'], threshold_price)

        # Если мы уже отправляли контроффер, но получили новый от покупателя
        elif latest_offer['creator'] == 'b' and latest_offer['state'] == 'n' and seller_counter_offer_sent:
            offer_amount = float(detailed_offer_data['latest_offer']['amount']['val'])

            # Если предложение покупателя ниже threshold_price, отклоняем его
            if offer_amount < first_counter_offer_price:
                # await self._make_counter_offer(detailed_offer_data['offer_id'], threshold_price)
                await self._decline_offer(detailed_offer_data['offer_id'])
            else:
                # Здесь можно будет принять предложение
                await self.accept_offer(detailed_offer_data['offer_id'])

    async def __insist_logik(self, detailed_offer_data):
        try:
            offer_state = detailed_offer_data['state']
            latest_offer = detailed_offer_data['latest_offer']
            offer_messages = detailed_offer_data['offer_messages']

            # Рассчитываем минимальную цену, ниже которой будем отменять предложения
            listing_price = float(detailed_offer_data['listings_info'][0]['price_amount']['val'])
            print(listing_price)

            # Проверяем, отправляли ли мы уже контроффер
            first_counter_offer_price = None
            for offer in offer_messages:
                if offer['creator'] == 's':
                    first_counter_offer_price = float(offer['amount']['val'])
                    break

            seller_counter_offer_sent = first_counter_offer_price is not None
            print(first_counter_offer_price)

            if offer_state == 'sp' and latest_offer['creator'] == 'b' and not seller_counter_offer_sent:
                # listing_price = float(detailed_offer_data['latest_offer']['amount']['val'])
                # counter_offer_price = round(listing_price * 0.9, 2)
                await self._make_counter_offer(detailed_offer_data['offer_id'], listing_price)

            # Если мы уже отправляли контроффер, но получили новый от покупателя
            elif latest_offer['creator'] == 'b' and latest_offer['state'] == 'n' and seller_counter_offer_sent:
                offer_amount = float(detailed_offer_data['latest_offer']['amount']['val'])

                # Если предложение покупателя ниже threshold_price, отклоняем его
                if offer_amount < first_counter_offer_price:
                    await self._make_counter_offer(detailed_offer_data['offer_id'], listing_price)
                    # await self._decline_offer(detailed_offer_data['offer_id'])
                else:
                    # Здесь можно будет принять предложение
                    await self.accept_offer(detailed_offer_data['offer_id'])
        except Exception as e:
            self.log.info(f"Function insist_logik ERROR {e}")
            return False

    async def _make_counter_offer(self, offer_id, counter_offer_price):
        try:
            # Находим кнопку Counter и кликаем по ней
            counter_button = self.page.locator('button[data-et-name="counter_offer"]')
            if not await counter_button.is_visible():
                self.log.info(f"Counter offer button not found for offer {offer_id}")
                return False

            await counter_button.click()
            await asyncio.sleep(2)  # Даем время модальному окну открыться

            # Вводим цену контрпредложения
            offer_input = self.page.locator('input[name="offer"]')
            if not await offer_input.is_visible():
                print(f"Offer input field not found for offer {offer_id}")
                return False

            await offer_input.fill(str(counter_offer_price))
            await asyncio.sleep(5)  # Небольшая задержка после заполнения

            # Нажимаем кнопку Submit для отправки контрпредложения
            submit_button = self.page.locator('button[data-et-name="submit"]')
            if not await submit_button.is_visible():
                print(f"Submit button not found for offer {offer_id}")
                return False

            await submit_button.click()
            await asyncio.sleep(2)  # Даем время для обработки запроса

            self.log.info(f"Counter offer of ${counter_offer_price} submitted for offer {offer_id}")
            return True

        except Exception as e:
            print(f"Error submitting counter offer for offer {offer_id}: {e}")
            return False

    async def _decline_offer(self, offer_id):
        try:
            # Находим и нажимаем кнопку Decline
            decline_button = self.page.locator('button[data-et-name="decline_offer"]')
            if not await decline_button.is_visible():
                print(f"Decline offer button not found for offer {offer_id}")
                return False

            await decline_button.click()
            await asyncio.sleep(2)  # Даем время для выполнения

            # Подтверждаем отмену оффера, если появляется подтверждающее модальное окно
            confirm_button = self.page.locator('button[data-et-name="yes"][data-et-on-name="decline_offer"]')
            if await confirm_button.is_visible():
                await confirm_button.click()
            await asyncio.sleep(2)
            self.log.info(f"Offer {offer_id} declined.")
            return True

        except Exception as e:
            print(f"Error declining offer {offer_id}: {e}")
            return False

    async def accept_offer(self, offer_id):
        self.log.info(f'Offer is equal or better than ours, accepting offer. {offer_id}')

    async def _get_sales_start_info(self):
        try:
            cur_responses = self._responses.copy()
            data_list = []
            for resp in cur_responses:
                data_list += resp['data']["sales_summary"]

            result = []

            for item in data_list:
                sale_date = datetime.strptime(item["inventory_booked_at"], "%Y-%m-%dT%H:%M:%S%z")
                product_info = {
                    "buyer_nickname": item["buyer"]["username"],
                    "order_id": item["id"],
                    "product_name": item["title"],
                    "product_price": float(item["total_price_amount"]["val"]),
                    "sale_date": sale_date.isoformat(),
                    "product_size": item["size_obj"]["id"],
                    'sku': None,
                    'user_id': 1,
                    "buyer_fb_id": item["buyer"]["fb_user_id"],
                    "sale_status": item["display_status"],
                    "order_url": f"https://poshmark.com/order/sales/{item['id']}",
                    "comment": ''
                }
                result.append(product_info)

            return result
        except Exception as e:
            print(e)

    async def check_for_sales(self, user_id):
        """Check for sales on marketplace"""
        self._string_for_collect = '/orders/sales'
        self._responses.clear()
        self.context.on('response', self._response_collector)
        await self.goto_page('https://poshmark.com/order/sales', referer='https://poshmark.com/feed', timeout=300000)
        await self.page.wait_for_load_state('load', timeout=450000)

        await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(5)
        resulst = await self._get_sales_start_info()
        if len(resulst) < 1:
            return
        items: list[dict] = resulst
        for item in items:
            try:
                await self.goto_page(item['order_url'], referer='https://poshmark.com/order/sales', timeout=300000)
                await asyncio.sleep(5)
                # url = await self.page.locator('link[rel="canonical"]').get_attribute('href')
                # item_id = url.split('/')[-1]
                # item['item_id'] = item_id             # TODO fix it later
                sku_text = await self.page.get_by_text('SKU: ').text_content()
                sku = sku_text.replace('SKU:', '').strip()
                item['user_id'] = user_id
                item['sku'] = sku
                # Находим и нажимаем на кнопку Download
                download_span = await self.page.wait_for_selector("span.m--l--3.tc--m.cursor--pointer", timeout=3000)
                if download_span:
                    await download_span.click()
                    await asyncio.sleep(2)  # Небольшая задержка, чтобы модальное окно успело появиться

                    # Находим и нажимаем на кнопку Download в модальном окне
                    download_button = await self.page.wait_for_selector('button:has-text("Download")', timeout=3000)
                    if download_button:
                        async with self.page.expect_download() as download_info:
                            await download_button.click()
                        download = await download_info.value

                        try:
                            # Сохраняем файл в нужную директорию
                            file_path = f"download/{download.suggested_filename}"
                            await download.save_as(file_path)
                            self.log.info(f"Downloaded file: {download.suggested_filename}")

                            # Обработка скачанного файла
                            auth_id = 'Ваш Auth ID'
                            auth_token = 'Ваш Auth Token'
                            person_info = gather_and_validate_adrress(file_path, auth_id, auth_token)

                            # Добавление информации в item
                            if person_info:
                                item['buyer_name'] = person_info.name
                                # Разбиваем адрес на строки, предполагая, что адрес в формате "улица, город"
                                # address_parts = person_info.address.split(',')
                                item['buyer_address_street1'] = person_info.address
                                item['buyer_city'] = person_info.city
                                if person_info.validation == False:
                                    item['comment'] = 'The customer address is not valid.'
                                item['image_data'] = base64.b64encode(person_info.images[0]).decode('utf-8')
                            else:
                                self.log.warning(f"Failed to extract person info from {download.suggested_filename}")

                        except Exception as e:
                            self.log.error(f"Error processing downloaded file for order {item['order_id']}: {e}")
                else:
                    print('No download button is found')
            except Exception as e:
                print(f"Error processing order {item['order_id']}: {e}")

        with open(os.path.join(os.getcwd(), 'sales_result.json'), 'w') as f:
            json.dump(resulst, f, indent=4)
        return resulst
        '''
        {
            "item_count": 2,
            "items_for_sale": [
                {
                    "site_item_id": null,
                    "order_id": "66a97f0a4f80f9993d6d3d36",
                    "price": 161.0,
                    "size": "8",
                    "original_item_url": "bootbarn.com/listing/2000404296.html",
                    "order_url": "https://poshmark.com/order/sales/66a97f0a4f80f9993d6d3d36",
                    "sku": "2000404296"
                },
                {
                    "site_item_id": null,
                    "order_id": "66a903980841b9049d45d497",
                    "price": 147.0,
                    "size": "11",
                    "original_item_url": "bootbarn.com/listing/2000274378.html",
                    "order_url": "https://poshmark.com/order/sales/66a903980841b9049d45d497",
                    "sku": "2000274378"
                }
            ]
        }
        '''

    def _extract_comments(self, data):
        def extract_actual_comment(message_):
            # Regular expression to extract text within quotes after "commented"
            match = re.search(r'commented.*: "([^"]+)"', message_)
            if match:
                return match.group(1)
            return message_

        comments_dict = {}

        for item in data['data']:
            news_items = item['content']['data']

            for news_item_data in news_items:
                news_item = news_item_data['news_item']
                message_id = news_item['id']
                product_id = news_item['target']['data'].get('bundle_id') or news_item['target']['data'].get('post_id')
                user = news_item['actor']['data'][0]
                user_id = user['id']
                user_name = user['full_name']
                raw_comment = news_item['message']
                actual_comment = extract_actual_comment(raw_comment)

                if product_id not in comments_dict:
                    comments_dict[product_id] = {}

                if user_id not in comments_dict[product_id]:
                    comments_dict[product_id][user_id] = {
                        "name": user_name,
                        "comments": []
                    }

                comments_dict[product_id][user_id]["comments"].append({
                    "message_id": message_id,
                    "comment": actual_comment
                })

        return comments_dict

    def merge_comment_dicts(self, dicts):
        merged_dict = defaultdict(lambda: defaultdict(lambda: {"name": "", "comments": []}))

        for d in dicts:
            for product_id, users in d.items():
                for user_id, details in users.items():
                    merged_dict[product_id][user_id]["name"] = details["name"]
                    merged_dict[product_id][user_id]["comments"].extend(details["comments"])

        return merged_dict

    async def get_comments(self):

        self._string_for_collect = '/newsfeed/comment?'
        self._responses.clear()
        self.context.on('response', self._response_collector)
        await self.goto_page('https://poshmark.com/news/comment', referer='https://poshmark.com/feed', timeout=300000)
        await self.page.wait_for_load_state('load', timeout=450000)
        await asyncio.sleep(5)
        await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(5)
        await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(5)
        cur_responsrs = self._responses.copy()
        coments_list = []
        for index, data in enumerate(cur_responsrs):
            comments = self._extract_comments(data)
            coments_list.append(comments)

        merged_dict = self.merge_comment_dicts(coments_list)
        with open(os_join(os.getcwd(), f'comment_{100500}.json'), 'w') as f:
            json.dump(merged_dict, f, indent=4)
