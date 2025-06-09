from api._category import Category_API
from api._product import Product_API
from api._website import Website_API
class API:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.product = Product_API(url,token)
        self.website = Website_API(url,token)
        self.category = Category_API(url,token)








            


    
