from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class ColorVariationDB(Base):
    __tablename__ = "color_variations"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    selected = Column(Boolean, default=False)
    image_url = Column(String, nullable=False)
    product_id = Column(String, ForeignKey("products.id"))


class SizeVariationDB(Base):
    __tablename__ = "size_variations"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    selected = Column(Boolean, default=False)
    available = Column(Boolean, default=True)
    stock_status = Column(String, nullable=False)
    shipping_info = Column(String, nullable=False)
    product_id = Column(String, ForeignKey("products.id"))


class ProductDetailsDB(Base):
    __tablename__ = "product_details"
    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey("products.id"))
    description_full_text_html = Column(Text, nullable=False)
    features_list = Column(Text, nullable=False)
    structured_features = Column(Text)


class ShippingReturnsDB(Base):
    __tablename__ = "shipping_returns"
    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey("products.id"))
    returns = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    restrictions = Column(Text)


class ProductDB(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    number = Column(String, nullable=False)
    images = Column(Text, nullable=False)
    variations = relationship("ColorVariationDB", backref="product")
    sizes = relationship("SizeVariationDB", backref="product")
    details = relationship("ProductDetailsDB", uselist=False, backref="product")
    shipping_returns = relationship("ShippingReturnsDB", uselist=False, backref="product")


class MetadataDB(Base):
    __tablename__ = "metadata"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_category_name = Column(String, nullable=False)
    parsed_category_url = Column(String, nullable=False)
    parser_timestamp = Column(String, nullable=False)
    total_products_saved = Column(Integer, nullable=False)
    parse_datetime_utc = Column(String, nullable=False)
