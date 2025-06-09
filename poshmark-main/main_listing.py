import argparse
import asyncio
import json
import os
from typing import Literal
from local_db.crud import  get_all_products
from poshmark.listing import PoshmarkListing
from poshmark.monitoringv3 import PoshmarkMonitoring
from poshmark.pproxy_controller import run_pproxy, kill_pproxy, get_free_port
from poshmark.validation import get_api_items
from api.api import API
from api.crud import to_product_dto
from config import Config
import random
import keyboard 
from accounts_api.connector import APIConnector, save_sale_info
from accounts_api.models import UserCreateRequest



async def run_browser(proxy: dict| str, listener_port, cooka, brow_type: Literal['L', 'T', 'M'] = 'T', safety_factor=4.0):
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
    match(brow_type):
        case 'L' | 'T':
            Browser = PoshmarkListing
        case 'M':
            Browser = PoshmarkMonitoring
    try:
        

        browser = Browser(
            headless=False,
            proxy_port=listener_port,
            UA_browser='Chrome',
            UA_system='Windows',
            UA_numb=2,
            safety_factor=safety_factor
        )


        await browser.run(url='https://poshmark.com/',cookies_path=cooka)
        await asyncio.sleep(5)
        return browser
    except Exception as e:
        print(e)
        if browser:
            await browser.save_cookies()
        print('Stop work and closing browser and kill pproxy process')
        try: await browser.close_browser()
        except:pass
        kill_pproxy(listener_port)
        pass






async def test_login(proxy: dict| str,  cooka: str, user_id, data: dict = None):
    listener_port = get_free_port()

    try:
        browser = await run_browser(
            proxy=proxy,
            listener_port=listener_port,
            cooka=cooka,
            brow_type='T'
        )
        keyboard.wait('ctrl+shift+q')


    except Exception as e:
        print(e)
    finally:
        try: 
            await browser.save_cookies()
        except:pass
        print('Stop work and closing browser and kill pproxy process')
        try: 
            await browser.close_browser()
        except:pass
        kill_pproxy(listener_port)
        pass



async def listing(proxy: dict| str,  cooka: str, data: dict, user_id, safety_factor=4.0):

    listing_count = data.get('listing_count')
    max_price = data.get('max_price')
    min_price = data.get('min_price')
    filter_category = data.get('filter_category')
    gender_category = data.get('gender_category')
    api_category = data.get('api_category')
    brand = data.get('brand')
    discount = data.get('discount')
    
    listing_addit_percent = data.get('listing_addit_percent')
    origin_addit_percent = data.get('origin_addit_percent')
    if discount:
        if not(isinstance(listing_addit_percent, int) or not isinstance(origin_addit_percent, int)):
            raise Exception('listing_addit_percent and origin_addit_percent must be int')
    else:
        if not (isinstance(listing_addit_percent, int)):
            raise Exception('listing_addit_percent must be int')
    
    availability = data.get('availability')
    new_condition = data.get('new_condition', False)
    
    if not availability:
        availability = 'N'
    elif availability not in ['N', 'S', 'D']:
        print(f'Wrong availability: {availability}, use N, S or D, default N')
        availability = 'N'
        
    listener_port = get_free_port()
    
    try:
        liseted_items_ids = ['2000368665', '0455H3', '04542J', '2000345767', '2000325570', '2000404296', '2000343127', '2000333565', '2000167888', '2000014395', '2000296019', '2000350572', '2000384162', '2000374772', '031063', '2000205441', '2000384596', '2000359684', '04541Q', '2000384165', '2000324612', '2000343130', '2000392831', '2000403080', '2000341144', '2000333559', '2000374734', '2000345746', '2000385772', '2000361444', '2000374762', '031064', '2000321523', '2000375716', '2000327383', '0454K1', '2000281766', '2000292260', '045295', '2000420686', '2000333270', '0456X9', '2000420690', '2000417601', '2000396949', '2000417598', '2000420688', '2000396976', '2000372418', '031514', '2000219702', '2000348187', '2000218833', '2000372416', '031654', '031655', '2000372393', '2000361447', '2000361448', '2000347101', '2000342260', '2000342300', '2000379128', '2000331589', '2000335476', '2000335468', '2000386735', '2000379130', '2000218023', '2000226185', '2000244723', '2000343137', '2000340414', '2000295819', '2000168847', '2000404206', '2000281829', '2000325567', '2000168849', '2000374728', '2000253629', '2000409887', '2000343136', '2000295820', '2000404962', '2000359654', '2000258935', '2000355199', '2000384095', '2000412900', '2000399803', '2000361033', '2000413264', '2000174562', '2000346806', '2000174564', '2000245042', '2000174563', '2000393406', '2000174567', '2000123167', '2000174565', '2000174566', '2000213834', '2000238285', '2000238529', '2000251557', '2000288324', '2000288819', '2000376393', '2000376395', '2000414401', '2000292261', '2000292263', '2000292285', '2000327384', '2000385080', '2000396943', '2000396944', '2000396945', '2000396946', '2000396947', '2000396948', '2000396950', '2000396951', '2000396974', '2000396977', '2000396978', '2000417586', '2000417599', '2000417558', '2000389536', '2000391149', '2000221254', '2000364092', '2000367591', '2000367595', '2000379631', '2000379636', '2000388814', '2000388815', '2000388845', '2000388883', '2000389386', '2000390855', '2000395336', '2000395337', '2000408241', '2000339274', '2000407759', '2000403535', '04515C', '045Y45', '2000381863', '2000399806', '2000412935', '04516R', '045Y42', '045Y43', '045Y46', '2000327444', '2000327447']
        liseted_items_ids += [itm.sku for itm in get_all_products()]
        min_count = listing_count + len(liseted_items_ids) * 2
        items = await get_api_items(
                min_count=min_count,
                min_price=min_price,
                max_price=max_price,
                filter_category=filter_category,
                gender_category=gender_category,
                api_category=api_category,
                brand = brand
            )
        items = [itm for itm in items if not itm.product_sku in liseted_items_ids]
        print(len(items))
        # Получаем список всех SKU из продуктов
        # api = APIConnector(base_url="http://127.0.0.1:8000")
        # skus_to_check = [itm.product_sku for itm in items]

        # # Проверяем наличие SKU в базе данных через API
        # existing_skus = api.check_skus_exists(skus_to_check)

        # Фильтруем продукты, исключая те, у которых SKU уже существуют в базе данных
        # items_to_add = [itm for itm in items if itm.product_sku not in existing_skus]
        random.shuffle(items)
        items_to_listing = items[5:listing_count+5]
        if len(items_to_listing) != listing_count:
            print(f'Not enough items to listing available: {len(items_to_listing)}')
        print(f'Will listed count: {len(items_to_listing)}')
        for item in items:
            print(item.category)
        # ===============
        # return None
        browser = await run_browser(
            proxy=proxy,
            listener_port=listener_port,
            cooka=cooka,
            brow_type='L',
            safety_factor=safety_factor
        )

        await browser.fill_items(
            user_id=user_id,
            items=items_to_listing,
            availability=availability,
            listing_addit_percent=listing_addit_percent,
            origin_addit_percent=origin_addit_percent,
            discount=discount,
            new_condition=new_condition,
        )


    except Exception as e:
        print(e)
    finally:
        await browser.save_cookies()
        print('Stop work and closing browser and kill pproxy process')
        try: await browser.close_browser()
        except:pass
        kill_pproxy(listener_port)
        pass

  

def parse_json(json_file: str):
    with open(os.path.join(os.getcwd(), json_file), 'r') as file:
        options = json.load(file)
        
    proxy_str = options.get('proxy_str')
    proxy_dict = options.get('proxy_dict')
    if not proxy_str and not proxy_dict:
        raise Exception('No proxy')
    
    proxy = proxy_str or proxy_dict
    
    cookies_path = options['cookies_path']
    absolute_path = cookies_path.get('absolute_path')
    relative_path = cookies_path.get('relative_path')
    data = options['data']
    mode = options.get('mode')
    safety_factor = options.get('safety_factor')
    
    if not absolute_path and not relative_path:
        raise Exception('No cookies_path')
    
    if not absolute_path:
        absolute_path = os.path.join(os.getcwd(), relative_path)

    cookies_path_ = absolute_path

    return proxy, cookies_path_, data, mode, safety_factor

async def gather_sales(proxy: dict| str,  cooka: str, user_id, data: dict = None):
    listener_port = get_free_port()

    try:
        browser = await run_browser(
            proxy=proxy,
            listener_port=listener_port,
            cooka=cooka,
            brow_type='M'
        )
        
        res = await browser.check_for_sales(user_id)
        res = [sale for sale in res if sale.get('buyer_address_street1')]
        api = APIConnector(base_url="http://fastapi_app:8093")
        # print(res)
        api.create_sales_bulk(res)

    except Exception as e:
        print(e)
    finally:
        try: await browser.save_cookies()
        except:pass
        print('Stop work and closing browser and kill pproxy process')
        try: await browser.close_browser()
        except:pass
        kill_pproxy(listener_port)
        pass

async def gather_offers(proxy: dict| str,  cooka: str, user_id, data: dict = None):
    listener_port = get_free_port()

    try:
        browser = await run_browser(
            proxy=proxy,
            listener_port=listener_port,
            cooka=cooka,
            brow_type='M'
        )
        res = await browser.check_offers(user_id)
        api = APIConnector(base_url="http://fastapi_app:8093")
        # api.create_products_bulk(res)

    except Exception as e:
        print(e)
    finally:
        try: await browser.save_cookies()
        except:pass
        print('Stop work and closing browser and kill pproxy process')
        try: await browser.close_browser()
        except:pass
        kill_pproxy(listener_port)
        pass

async def change_prices(proxy: dict| str,  cooka: str, user_id, data: dict = None):
    listing_addit_percent = data.get('listing_addit_percent')
    origin_addit_percent = data.get('origin_addit_percent')
    listener_port = get_free_port()

    try:
        browser = await run_browser(
            proxy=proxy,
            listener_port=listener_port,
            cooka=cooka,
            brow_type='M'
        )
        
        orig_milti = (1 +  (origin_addit_percent / 100))
        listing_milti = (1 +  (listing_addit_percent / 100))
        
        items_from_site = browser.get_items_from_site()
        print(len(items_from_site))
        # print(items_from_site)
        for item_id, item in items_from_site.items():
            old_origin_price = item['original_price_amount']
            old_listing_price = item['price_amount']
            print("=" * 50)
            print(f'Item id - {item_id}')
            print("Price: ", old_listing_price)
            # print(f'Old_origin_price= {old_origin_price}')
            # print(f'Old_listing_price= {old_listing_price}')
            item_edit_url = f'https://poshmark.com/edit-listing/{item_id}'
            print(item_edit_url)
            new_op = old_origin_price * orig_milti
            new_lp = old_listing_price * listing_milti
            # print(f'New origin price = {new_op}')
            # print(f'New listing price = {new_lp}')
            # , int(new_op), int(new_lp)
            if old_listing_price < 100:
                print("Delete")
                await browser.delete_listing(item_edit_url)
                break
        

    except Exception as e:
        print(e)
    finally:
        try: await browser.save_cookies()
        except:pass
        print('Stop work and closing browser and kill pproxy process')
        try: await browser.close_browser()
        except:pass
        kill_pproxy(listener_port)
        pass

async def item_monitor_with_db(proxy: dict| str,  cooka: str, user_id, data: dict = None):
    listener_port = get_free_port()

    try:
        browser = await run_browser(
            proxy=proxy,
            listener_port=listener_port,
            cooka=cooka,
            brow_type='M'
        )
        api = APIConnector(base_url="http://fastapi_app:8093")
        items_from_site = browser.get_items_from_site()
        print(len(items_from_site))
        # print(items_from_site)
        for item_id, item in items_from_site.items():
            await asyncio.sleep(2)
            res = api.item_exists(item_id)
            print(f'Item: {item_id} {res}')
            if not res:
                
                item_edit_url = f'https://poshmark.com/edit-listing/{item_id}'
                item = await browser._gather_information_item(item_edit_url)

                item['user_id'] = user_id
                item['api_id'] = 0
                print(item)
                api.create_products_bulk([item])
                await asyncio.sleep(10)

                

        

    except Exception as e:
        print(e)
    finally:
        try: await browser.save_cookies()
        except:pass
        print('Stop work and closing browser and kill pproxy process')
        try: await browser.close_browser()
        except:pass
        kill_pproxy(listener_port)
        pass
   

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Poshmark tools.')
    parser.add_argument('json_file', type=str, help='Json with all options for start.')
    args = parser.parse_args()
    # 185.97.146.97:8093
    api = APIConnector(base_url="http://127.0.0.1:8000")  # http://fastapi_app:8093
    user = api.get_user(store_name="poshmark", username="Christopher Sullivan")
    proxy, cookies, data, mode, safety_factor = parse_json(args.json_file)
    proxy = user.proxy
    cookies = user.cookies
    user_id = user.id

    mode = 'listing'
    with open('cookies.json', 'w') as file:
        json.dump(cookies, file, indent=4)
    print(proxy)
    if mode == 'listing':
        asyncio.run(listing(proxy, 'cookies.json', data, user_id, safety_factor=safety_factor))
    elif mode == 'test_login':

        asyncio.run(test_login(proxy, 'cookies.json', data, user_id))
        # api.update_user_cookies(user_id, cookies_data)
    elif mode == 'monitoring':
        asyncio.run(gather_sales(proxy, 'cookies.json', user_id))

    elif mode == 'change_prices':
        asyncio.run(change_prices(proxy, 'cookies.json', user_id, data))
    else:
        raise Exception(f'Wrong mode, {mode} not valid mode type, use "listing" or "test_login"')

