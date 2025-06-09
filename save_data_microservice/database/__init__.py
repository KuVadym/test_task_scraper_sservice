from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
import logging



#================================= SQLite =====================================
engine = create_engine(
    "sqlite:///test.db", connect_args={"check_same_thread": False}, echo=True
)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()

def init_db():
    from database.form_models import Form
    
    Base.metadata.create_all(bind=engine)
