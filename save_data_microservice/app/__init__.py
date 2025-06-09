from fastapi import FastAPI
from app.udate_day_activity import save_to_db_apir

from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)



app = FastAPI()
app.include_router(save_to_db_apir)