from app import cipher

def decrypt_data(data: str) -> str:
    return cipher.decrypt(data.encode()).decode()