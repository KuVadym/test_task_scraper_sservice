import requests
from .models import UserCreateRequest, UserResponse, User
from .exceptions import APIError, NotFoundError
from typing import List, Union, Dict

class APIConnector:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = 'token'
    
    def create_user(self, user_data: UserCreateRequest) -> dict:
        url = f"{self.base_url}/user/"
        headers = {
            "Authorization": f"Bearer {self.token}"
        } 
        response = requests.post(url, json=user_data.dict(), headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise NotFoundError(detail=response.json().get('detail', 'Not found'))
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))

    def get_user(self, store_name: str, username: str) -> UserResponse:
        url = f"{self.base_url}/user/{store_name}/{username}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        } 
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return UserResponse(**response.json())
        elif response.status_code == 404:
            raise NotFoundError(detail=response.json().get('detail', 'Not found'))
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))

    def get_all_users_by_market(self, store_name: str) -> List[User]:
        url = f"{self.base_url}/users/{store_name}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        } 
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            return [User(**user_data) for user_data in users]
        elif response.status_code == 404:
            raise NotFoundError(detail=response.json().get('detail', 'Not found'))
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))
        
    def create_sales_bulk(self, sales_data: list) -> dict:
        url = f"{self.base_url}/sales/bulk/"
        headers = {
            "Authorization": f"Bearer {self.token}"
        } 
        response = requests.post(url, json=sales_data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))
        
    def create_products_bulk(self, products_data: list) -> dict:
        url = f"{self.base_url}/products/bulk/"
        headers = {
            "Authorization": f"Bearer {self.token}"
        } 
        response = requests.post(url, json=products_data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))
        
    def update_user_cookies(self, user_id: int, cookies: Union[Dict, List]) -> dict:
        url = f"{self.base_url}/user/{user_id}/cookies"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.put(url, json={"cookies": cookies}, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise NotFoundError(detail=response.json().get('detail', 'Not found'))
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))

    def create_offer(self, offer_data: dict) -> dict:
        url = f"{self.base_url}/offer/"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.post(url, json=offer_data, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise NotFoundError(detail=response.json().get('detail', 'Not found'))
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))

    def create_offers_bulk(self, offers_data: list) -> dict:
        url = f"{self.base_url}/offers/bulk/"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.post(url, json=offers_data, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise NotFoundError(detail=response.json().get('detail', 'Not found'))
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))
        
    def check_skus_exists(self, skus: List[str]) -> List[str]:
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.post(f"{self.base_url}/products/check_skus/", json={"skus": skus}, headers=headers)
        if response.status_code == 200:
            return response.json().get("existing_skus", [])
        else:
            raise Exception("Failed to check SKUs")
        
    def get_sale(self, sale_id: int) -> dict:
        url = f"{self.base_url}/sale/{sale_id}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise NotFoundError(detail="Sale not found")
        else:
            raise APIError(response.status_code, response.json().get('detail', 'Error'))
        
    def item_exists(self, item_id: str) -> bool:
        """Проверяет, существует ли товар с заданным item_id в базе данных через API."""
        url = f"{self.base_url}/item_exists"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {
            "item_id": item_id
        }
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            # Ожидаем, что API возвращает JSON с полем "exists"
            return response.json().get("exists", False)
        else:
            raise Exception(f"Error checking item existence: {response.status_code} - {response.text}")

    def get_user_by_id(self, user_id: int):
        """
        Метод для получения информации о пользователе по user_id.
        """
        url = f"{self.base_url}/user_get_by_id/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()  # Возвращаем данные пользователя в формате JSON
        elif response.status_code == 404:
            print("User not found.")
            return None
        else:
            print(f"Failed to get user data. Status code: {response.status_code}")
            return None

    def get_products_by_sku(self, sku: str):
        """
        Метод для получения информации о продуктах по SKU через API.
        """
        try:
            headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
            }
            response = requests.get(f"{self.base_url}/products/by_sku/{sku}", headers = headers)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to fetch products, status code: {response.status_code}")
        except Exception as e:
            print(f"Error in get_products_by_sku: {str(e)}")
            return []

    def product_withdrawn(self, item_id: str) -> bool:
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            body = {
                "item_id": item_id
            }
            response = requests.post(f"{self.base_url}/products/withdrawn/", headers=headers, json=body)
            if response.status_code == 200:
                return response.json().get("status", False)
            else:
                return False
        except Exception:
            return False


import os
import base64
#Тесты скачивания картинки с бд sales
def save_sale_info(api_connector, sale_id, output_directory="output"):
    # Шаг 1: Получение данных о заказе
    sale_data = api_connector.get_sale(sale_id)

    # Шаг 2: Сохранение изображения на диск
    image_data_base64 = sale_data.get("image_data")
    if image_data_base64:
        # Декодирование данных из Base64
        image_data = base64.b64decode(image_data_base64)

        # Создание директории для сохранения файла, если она не существует
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Формирование пути к файлу
        image_filename = f"sale_{sale_id}_image.jpg"
        image_filepath = os.path.join(output_directory, image_filename)

        # Сохранение изображения в файл
        with open(image_filepath, "wb") as image_file:
            image_file.write(image_data)

        # Заменяем `image_data` на путь к файлу в данных заказа
        sale_data["image_data"] = image_filepath
    else:
        sale_data["image_data"] = "No image available"

    # Шаг 3: Вывод информации о заказе в консоль
    print("Order Information:")
    for key, value in sale_data.items():
        print(f"{key}: {value}")
