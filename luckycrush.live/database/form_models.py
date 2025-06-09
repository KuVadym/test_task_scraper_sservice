from flask_login import UserMixin
from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.sqltypes import DateTime

from database import Base


class Form(Base, UserMixin):
    __tablename__ = "luckycrush_forms"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    form_id = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    first_activity = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    time_online = Column(Integer)