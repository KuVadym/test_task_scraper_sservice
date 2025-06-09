import re
import random
from accounts_api.connector import APIConnector
from api.api import API
from api.crud import get_category
from api.dto import ProductDTO
from config import Config


def contains_trademark_symbols(text):
    pattern = r'[\u2122\u00AE\u00A9\u2120]'

    # Ищем совпадения в тексте
    match = re.search(pattern, text)

    # Возвращаем True, если найдено совпадение, иначе False
    return bool(match)


def valid_itm(item):
    title = bool(item.title)
    description = bool(item.description)
    iamges_urls = all(item.images)
    size = bool(item.poshmark_sizes)
    if contains_trademark_symbols(item.title) or contains_trademark_symbols(item.description):
        return False
    if isinstance(item.price, str):
        cleaned_price = re.sub(r'[^0-9.]', '', item.price)
    else:
        cleaned_price = isinstance(item.price, float) or isinstance(item.price, int)
    # if item.price:
    #     need_price = min_price < float(item.price) < max_price
    # else:
    #     return False
    valid_category = item.poshmark_category
    if not valid_category:
        return False

    return all([title, description, cleaned_price, iamges_urls, size, valid_category])


async def get_api_items(
        min_count: int = 100,
        gender_category=None,
        filter_category=None,
        min_price: int = None,
        max_price: int = None,
        api_category: str = None,
        brand=None,
        sub_category_need=True
) -> list[ProductDTO]:
    api = API(Config.API_URL, Config.API_TOKEN)
    api_seller = APIConnector('http://fastapi_app:8093')
    # if api_category:
    # categories = await api.category.get_categories()
    # items = []
    # without_sub_category = []
    # # print(f'all category count: {len(categories)}')
    # for category in categories:
    #     valid_category_names = get_category(api_category.split('-'))
    #     if not valid_category_names:
    #         continue
    #     if sub_category_need and not all(valid_category_names):
    #         continue

    #     if gender_category or category:
    #         category_filter = []
    #         if gender_category:
    #             category_filter.append(gender_category in valid_category_names)
    #         if filter_category:
    #             category_filter.append(filter_category in valid_category_names)
    #     else:
    #         category_filter = [True]
    #     if not all(category_filter):
    #         continue

    # category_items = []
    # api_items = await api.product.get_products(category = api_category, min_price=min_price, max_price=max_price, brand=brand)
    # category_items += api_items
    # index = 2
    # while len(api_items) > 199:
    #     api_items = await api.product.get_products(category = api_category,  min_price=min_price, max_price=max_price, brand=brand, page=index)
    #     category_items += api_items
    #     index += 1

    # if sub_category_need and not all(valid_category_names):
    #     without_sub_category += api_items
    #     continue

    # if not api_items:
    #     continue
    # valid = list(filter(
    #     lambda x: valid_itm(x, ),
    #     category_items
    # ))

    # items += valid
    # if len(items) > min_count:
    #     break

    # return api_items

    categories = await api.category.get_categories()
    items = []
    without_sub_category = []
    # print(f'all category count: {len(categories)}')
    for category in categories:
        valid_category_names = get_category(category['name'].split('-'))
        # print(valid_category_names)
        if not valid_category_names:
            continue
        if sub_category_need and not all(valid_category_names):
            continue

        if gender_category or category:
            category_filter = []
            if gender_category:
                category_filter.append(gender_category in valid_category_names)
            if filter_category:
                category_filter.append(filter_category in valid_category_names)
        else:
            category_filter = [True]
        if not all(category_filter):
            continue

        category_items = []
        api_items = await api.product.get_products(category=category['name'], min_price=min_price, max_price=max_price,
                                                   brand=brand)
        category_items += api_items
        index = 2
        while len(api_items) > 199:
            api_items = await api.product.get_products(category=category['name'], min_price=min_price,
                                                       max_price=max_price, brand=brand, page=index)
            category_items += api_items
            index += 1

        if sub_category_need and not all(valid_category_names):
            without_sub_category += api_items
            continue

        if not api_items:
            continue
        skus = [item.product_sku for item in category_items]
        skus_check = api_seller.check_skus_exists(skus=skus)
        category_items_filter = []
        for item in category_items:
            if item.product_sku in skus_check:
                continue
            category_items_filter.append(item)
        valid = list(filter(
            lambda x: valid_itm(x, ),
            category_items_filter
        ))
        items += valid
        if len(items) > min_count:
            break
        # print(items)

    return items
