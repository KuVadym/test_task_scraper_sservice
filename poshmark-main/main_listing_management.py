from poshmark.listing_management import PoshmarkProductManager
import asyncio
from accounts_api.connector import APIConnector
from poshmark.listing import PoshmarkListing
from poshmark.monitoringv3 import PoshmarkMonitoring
from typing import Literal
from api.api import API
from config import Config
from poshmark.pproxy_controller import run_pproxy, kill_pproxy, get_free_port
import json
import argparse


async def run_browser(proxy: dict | str, listener_port, cooka, brow_type: Literal['L', 'T', 'M'] = 'T'):
    print(f'local proxy port: {listener_port}')
    if isinstance(proxy, dict):
        host = proxy.get('host')
        username = proxy.get('username')
        password = proxy.get('password')
        run_pproxy(
            listen_port=listener_port,
            host=host,
            username=username,
            password=password
        )
    else:
        run_pproxy(
            listen_port=listener_port,
            proxy=proxy
        )

    await asyncio.sleep(10)

    Browser = PoshmarkProductManager

    try:

        browser = Browser(
            headless=True,
            proxy_port=listener_port,
            UA_browser='Chrome',
            UA_system='Windows',
            UA_numb=2,
        )

        await browser.run(url='https://poshmark.com/', cookies_path=cooka)
        await asyncio.sleep(5)
        return browser
    except Exception as e:
        print(e)
        if browser:
            await browser.save_cookies()
        print('Stop work and closing browser and kill pproxy process')
        try:
            await browser.close_browser()
        except:
            pass
        kill_pproxy(listener_port)
        pass


async def main(sku):
    # Пример SKU для поиска
    #sku = "2000394899"
    # Инициализация менеджера продуктов
    product_manager = PoshmarkProductManager()
    # Получение списка продуктов по SKU
    data = await product_manager.gather_data(sku)
    for user_id, user_data in data.items():
        account_info = user_data['account_info']
        products = user_data['products']

        proxy = account_info['proxy']
        cookies = account_info['cookies']

        # Сохраняем куки в файл
        with open(f'cookies.json', 'w') as file:
            json.dump(cookies, file, indent=4)

        print(f"Starting session for user_id: {user_id} with proxy: {proxy}")

        listener_port = get_free_port()

        try:
            browser = await run_browser(
                proxy=proxy,
                listener_port=listener_port,
                cooka='cookies.json',
                brow_type='M'
            )
            for product in products:
                product_url = product['item_url']
                print(f"Processing product URL: {product_url}")
                await browser.delete_listing(product_url)
                # Здесь можно вывать метод для работы с продуктом, например:
                status_db = product_manager.accounts_api.product_withdrawn(product['item_id'])
                print(f"Withdrawn product ID: {product['item_id']} STATUS => {status_db}")
                await asyncio.sleep(5)
        except Exception as e:
            print(e)
        finally:
            try:
                await browser.save_cookies()
            except:
                pass
            print('Stop work and closing browser and kill pproxy process')
            try:
                await browser.close_browser()
            except:
                pass
            kill_pproxy(listener_port)
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Передачи SKU параметра в скрипт.")

    # Добавляем аргументы
    parser.add_argument('sku', type=str, help="SKU параметр")

    # Читаем аргументы
    args = parser.parse_args()
    print(args.sku)
    asyncio.run(main(args.sku))
