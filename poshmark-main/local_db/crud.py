from .db_init import get_db
from .models import User, Product


def create_user(name: str, cookies: list) -> User:
    with get_db() as db:
        user = User(name=name, cookie=cookies)
        db.add(user)
        db.commit()
        db.refresh(user)  # Ensure the user is refreshed from the database
        return user

def get_user_by_name(name: str) -> User | None:
    with get_db() as db:
        user = db.query(User).filter(User.name == name).first()
        return user
    
def create_product(product: Product) -> Product:
    with get_db() as db: 

        db.add(product)
        db.commit()
        return product

def get_all_products() -> list[Product|None]:
    with get_db() as db:
        products = db.query(Product).all()
        print(products)
        return products

def get_product_by_user(user: User) -> list[Product|None]:
    if not user:
        return list()
    with get_db() as db:
        return db.query(Product).filter(Product.user_id == user.id).all()

def get_products_by_ids(product_ids):
    with get_db() as db:
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        return products