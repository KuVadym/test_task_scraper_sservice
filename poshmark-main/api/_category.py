import inspect
import json
import os
import aiohttp
from api.crud import to_category_dto
from api.dto import CategoryDTO


class Category_API:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token


    async def get_category(self, category_id: int) -> dict:
        """
        Get a category by ID

        Args:
            category_id (int): Category ID

        Returns:
            CategoryDTO: Category details
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.token}"}
                async with session.get(f"{self.url}/category/{category_id}", headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as ex:
            print(inspect.currentframe().f_code.co_name, ex)
            
    async def get_categories(self) -> dict:#-> list[CategoryDTO]:
        """
        Get a category by ID

        Args:
            category_id (int): Category ID

        Returns:
            CategoryDTO: Category details
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.token}"}
                async with session.get(f"{self.url}/categories", headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as ex:
            print(inspect.currentframe().f_code.co_name, ex)

    async def update_category(self, category_id: int, data: dict) -> dict:
        """
        Update a category

        Args:
            category_id (int): Category ID
            data (dict): Updated category data

        Returns:
            dict: Response with update status
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with session.put(f"{self.url}/category/{category_id}", json=data, headers=headers) as response:
                response.raise_for_status()
                return await response.json()