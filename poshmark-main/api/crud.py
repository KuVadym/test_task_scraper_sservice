import json
import os
from api.dto import CategoryDTO, ProductDTO, VariantDTO,  WebsiteDTO
from copy import deepcopy

with open(os.path.join(os.getcwd(),'category_json.json'), 'r') as f:
    data = json.load(f)
    
with open(os.path.join(os.getcwd(),'women_shoes_category.json'), 'r') as f:
    women_category = json.load(f)
    

def get_category(category_list: list[str]):
    category_dict: dict = deepcopy(data)
    full_category = '-'.join(category_list)
    if full_category in women_category.keys():
        if women_category[full_category] == 'boots':
            return ['women', 'shoes', None] 
        return ['women', 'shoes', women_category[full_category]]
    
    def woman_shoes_is(full_category):
        all_ws = women_category['woman_all_shoes']
        if full_category in all_ws:
            return ['women', 'shoes', None]
        
    def get_main_category(main_keys):
        if 'womens' in category_list:
            return 'women'
        if 'mens' in category_list:
            return 'men'
        for key in main_keys:
            if key in category_list:
                return key        
            
        return None
    

    def get_aditional_category(aditional_cat_list):
        for key in aditional_cat_list:
            for cat in category_list:
                if key in cat:
                    return key

    def get_sub_category( sub_category_keys):
        for key in sub_category_keys:
            for cat in category_list:
                if key in cat:
                    return key
        return None


    category_list = list(map(lambda x: x.strip().lower(), category_list))
    main_keys = category_dict.keys()
    main_category = get_main_category(main_keys)
    if main_category is None:
        return 
    maint_category_dict = category_dict[main_category]
    aditional_category_list = maint_category_dict.pop('aditional')
    
    syb_category_list = maint_category_dict.keys()
    sub_category = get_sub_category(syb_category_list)
    aditional_category = None
    if sub_category and not isinstance(maint_category_dict[sub_category], str):
        aditional_category = get_aditional_category(aditional_category_list)
    elif sub_category:
        aditional_category = maint_category_dict[sub_category]
    else:
        aditional_category = get_aditional_category(aditional_category_list)
    if not aditional_category:
        return woman_shoes_is(full_category)
    return [main_category, aditional_category, sub_category]



def to_variant_dto(variant_data: dict) -> VariantDTO:

    price_adjustment = variant_data['price_adjustment']
    quantity = variant_data['quantity']
    variant_id = variant_data['id']
    options = variant_data['options']
    size = None
    color = None
    url = None
    for opt in options:
        name = opt['option_name']
        match(name):
            case 'color':
                if color:
                    print('here')
                color = opt['option_value']
            case'size':
                size = opt['option_value']
            case 'url':
                url = opt['option_value']
            
    images = variant_data.get('variantImages')
    variant = VariantDTO(
        quantity=quantity,
        price_adjustment=price_adjustment,
        id=variant_id,
        size=size,
        color=color,
        variant_images=images,
        url=url,
    )
    return variant



def to_product_dto(data: dict) -> ProductDTO:
    try:
        if 'item' in data:
            data = data['item']
        api_dict = deepcopy(data)
        title = data.pop("title")
        description = data.pop("description")
        
        platform = data.pop("platform")
        

        created_at = data.pop("created_at")
        updated_at = data.pop("updated_at")
        
        
        category = data.pop("category")
        category_name = category['name']
        
        images = data.pop("images")
        product_id = data.pop("id")
        price = data.pop('base_price')
        
        brand = data.pop('brand')
        brand_name = brand['name']
        url = data.pop('url')
        if 'product_id' in data:
            product_sku = data.pop('product_id')
        else:
            product_sku = data.pop('sku')
        
        other_data = {}

        poshmark_category = get_category(category_name.split('-'))
        variants = []
        if "variants" in data:
            variants_ = data.pop("variants")
            for variant in variants_:
                var = to_variant_dto(variant)
                variants.append(var)

        if data:
            for otehr_key, val in data.items():
                other_data[otehr_key] = val
    
        product_dto = ProductDTO(
            title=title,
            description=description,
            platform=platform,
            created_at=created_at,
            updated_at=updated_at,
            category=category,
            images=images,
            variants=variants,
            id=product_id,
            url=url,
            other_data=other_data,
            price=price,
            product_sku=product_sku,
            api_dict=api_dict,
            poshmark_category=poshmark_category,
            brand=brand_name,
            
        )
        if not 'color_dict' in product_dto.other_data:
            return [product_dto]
        products = []
        for color_, parametr_dict in product_dto.other_data['color_dict'].items():
            porduct_copy = deepcopy(product_dto)
            
            porduct_copy.images = list(set(parametr_dict['images']))
            if not porduct_copy.images:
                continue
            porduct_copy.poshmark_sizes = parametr_dict['sizes']
            porduct_copy.poshmark_color = list(parametr_dict['poshmark_color']) if parametr_dict['poshmark_color'] else []
            porduct_copy.variant_ids = parametr_dict['variant_ids']
            porduct_copy.variant_color = color_
            products.append(porduct_copy)

            
        return products
    except Exception as ex:
        print(ex, product_id, product_sku)
        return None

def to_website_dto(data) -> WebsiteDTO:
    name = data.pop("name")
    url = data.pop("url")
    website_id = data.pop("id")
    return WebsiteDTO(name=name, url=url,id=website_id)


def to_category_dto(data) -> CategoryDTO:
    name = data.pop("name")
    category_id = data.pop('id')
    return CategoryDTO(name=name, id=category_id)

def get_many_products(data=None, *, products=None):
    if not 'products' in data and not products:
        raise ValueError("Response does not consis products")
    if data:
        products = data['products']
    products_dto = []
    for product in products:
        products_dto += to_product_dto(product)
    return products_dto







