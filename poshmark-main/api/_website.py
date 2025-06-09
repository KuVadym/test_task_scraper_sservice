import json
import os
import aiohttp
from api.crud import to_website_dto
from api.dto import  WebsiteDTO


class Website_API:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token


    async def get_website(self, website_id: int) -> dict:
        """
        Get a website by ID

        Args:
            website_id (int): Website ID

        Returns:
            WebsiteDTO: Website details
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with session.get(f"{self.url}/website/{website_id}", headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                return await response.json()

    async def update_website(self, website_id: int, data: dict) -> dict:
        """
        Update a website

        Args:
            website_id (int): Website ID
            data (dict): Updated website data

        Returns:
            dict: Response with update status
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with session.put(f"{self.url}/website/{website_id}", json=data, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
            
    async def get_websites(self):

        """
        Get a websites

        Returns:
            list[WebsiteDTO]: Website details
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}

            async with session.get(f"{self.url}/websites", headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                if not data:
                    print(await response.text())
                return data
                return to_website_dto(data)