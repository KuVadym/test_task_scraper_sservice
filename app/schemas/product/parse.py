from typing import Any, Dict, List, Optional

from pydantic import BaseModel, HttpUrl


class ColorVariation(BaseModel):
    name: str
    selected: bool
    id: str
    image_url: HttpUrl


class SizeVariation(BaseModel):
    name: str
    id: str
    selected: bool
    available: bool
    stock_status: str
    shipping_info: str


class Variations(BaseModel):
    colors: Optional[List[ColorVariation]]
    sizes: List[SizeVariation]


class ShippingReturns(BaseModel):
    returns: str
    message: str
    restrictions: Optional[List[Dict[str, Any]]] = None


class ProductDetails(BaseModel):
    description_full_text_html: str
    features_list: List[str]
    structured_features: Optional[Dict[str, str]] = None


class VariationsDataJson(BaseModel):
    color: Dict[str, str]
    size: Dict[str, str]


class Product(BaseModel):
    name: str
    price: str
    brand: str
    number: str
    product_details: ProductDetails
    variations: Optional[Variations] = None
    shipping_returns: ShippingReturns
    images: List[HttpUrl]
    variations_data_json: VariationsDataJson


class Metadata(BaseModel):
    source_category_name: str
    parsed_category_url: HttpUrl
    parser_timestamp: str
    total_products_saved: int
    parse_datetime_utc: str


class ProductsResponse(BaseModel):
    metadata: Metadata
    products: Dict[HttpUrl, Product]
