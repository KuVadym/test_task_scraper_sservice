from .db_init import Base

from sqlalchemy import JSON, Column, ForeignKey, Integer, ClauseList, String
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    proxy = Column(String )
    cookie = Column(JSON, nullable=False)

    products = relationship("Product", back_populates="owner")

 


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    id_in_shop = Column(String, nullable=False)    
    edit_url = Column(String, nullable=True)
    api_id = Column(Integer, nullable=False)
    sku = Column(String, nullable=True)
    variant_color = Column(String, nullable=False)
    variant_ids = Column(JSON, nullable=True)
    listed_json = Column(JSON, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="products")

