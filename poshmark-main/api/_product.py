import inspect
import json
from math import e
import os
import re
import aiohttp
from api.crud import get_many_products, to_product_dto
from api.dto import ProductDTO
from urllib.parse import urljoin

class Product_API:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token

    async def get_product(self, product_id: int) -> dict:
        """
        Get a product by ID

        Args:
            product_id (int): Product ID

        Returns:
            ProductDTO: Product details
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.token}"}
            
                async with session.get(urljoin(self.url, f'product/{product_id}'), headers=headers) as response:
                    if response.status == 200:
                        return  await response.json()
                    else:
                        response.raise_for_status()
        except Exception as e:
            print('error: ', e)

    async def create_product(self, data: dict) -> dict:
        """
        Create a new product

        Args:
            data (dict): Product data

        Returns:
            dict: Response with product ID
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}

            async with session.post(url=urljoin(self.url, 'product'), json=data, headers=headers) as response:
                response.raise_for_status()
                return await response.json()

    async def update_product(self, product_id: int, data: dict) -> dict:
        """
        Update a product

        Args:
            product_id (int): Product ID
            data (dict): Updated product data

        Returns:
            dict: Response with update status
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with session.put(url=urljoin(self.url, f'product/{product_id}'), json=data, headers=headers) as response:
                response.raise_for_status()

                return response.json()
    ''' ids: Optional[str] = None,
        platform: Optional[str] = None
        category: Optional[str] = None
        brand: Optional[str] = None
        sku: Optional[str] = None
        min_price: Optional[float] = None
        max_price: Optional[float] = None
        limit: int = Field(10, ge=1)
        offset: int = Field(1, ge=1)'''

    async def get_products(
            self,
            *,
            platform: str = None,
            category: str = None,
            min_price: float = None, 
            max_price: float = None,
            page: int = 1,
            limit: int = 200,
            offset: int = None,
            as_dict = False,
            brand = None
        ) -> (list[ProductDTO], int):
        """
        Get a list of products

        Args:
            platform (str): Platform name (optional)
            category (str): Category name (optional)
            min_price (float): Minimum price filter (optional)
            max_price (float): Maximum price filter (optional)
            page (int): Page number (optional)
            limit (int): Limit of products per page (optional)
            offset (int): Offset for pagination (optional)
            json_filter (dict): JSON filter (optional)
        Returns:
            list[ProductDTO]: List of products
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        if offset is None:
            offset = (page - 1) * limit

        params = {
            "limit": limit
        }
        
        if offset > 0:
            params["offset"] = offset
        if platform:
            params["platform"] = platform
        if category:
            params["category"] = category.replace("/", ",")
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if brand is not None:
            params['brand'] =  brand

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=urljoin(self.url, 'products'), headers=headers, params=params) as response:
                    if response.status == 200:
                        if as_dict:
                            return await response.json()
                        products = get_many_products(await response.json())
                        return products
                    else:
                        print(f"Ошибка: {response.status}")
                        print(await response.text())
                        return None
        except aiohttp.ClientError as client_error:
            print(f"Ошибка клиента: {client_error}")
        except ValueError as val_er:
            print(f"Ошибка: {val_er}")
        except Exception as unk_er:
            print(f'[{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}]', unk_er)


                
    async def create_products(self, products: list) -> dict:
        """
        Create new products

        Args:
            products (list): List of product dictionaries

        Returns:
            dict: Response from the API
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
            async with session.post(f"{self.url}/products", headers=headers, data=json.dumps(products)) as response:
                response.raise_for_status()
                return await response.json()
                return data

    async def update_products(self, products: list) -> dict:
        """
        Update existing products

        Args:
            products (list): List of product dictionaries with product_id

        Returns:
            dict: Response from the API
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
            async with session.put(f"{self.base_url}/products", headers=headers, data=json.dumps(products)) as response:
                response.raise_for_status()
                return await response.json()