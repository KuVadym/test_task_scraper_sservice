from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


SQLALCHEMY_DATABASE_URL = "sqlite:///./poshmark/sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables_if_not_exists():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    user_create = '''
    CREATE TABLE users (
        id INTEGER NOT NULL,
        name VARCHAR,
        proxy VARCHAR,
        cookie JSON NOT NULL,
        PRIMARY KEY (id)
    );
    '''
    products_create = '''
    CREATE TABLE products (
    id INTEGER NOT NULL PRIMARY KEY,
    id_in_shop VARCHAR NOT NULL,
    edit_url VARCHAR,
    api_id INTEGER NOT NULL,
    sku VARCHAR,
    variant_color VARCHAR NOT NULL,
    variant_ids JSON,
    listed_json JSON NOT NULL,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
    );
    '''
    
    
    with engine.connect() as connection:
        if 'users' not in tables:
            connection.execute(text(user_create))
        if 'products' not in tables:
            connection.execute(text(products_create))

create_tables_if_not_exists()



