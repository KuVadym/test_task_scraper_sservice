import logging
import os
import aiofiles
import hashlib
from dotenv import load_dotenv

load_dotenv()

class Config:
    LOGGING_LEVEL = logging.INFO
    OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')
    ENGINE_TEXT = os.getenv('ENGINE_TEXT')
    
    SAVE_RESPONSE_FOR_TEST: bool = True
    MOCK_RESPONSE_DATA: bool = False 
    API_TOKEN = 'NOKEN'
    API_URL = 'http://185.97.146.97:8091'




def mock_response(do_mock: bool = False):
    def outer_wraper(func):
        if not do_mock:
            return func
        async def inner_wraper(*args, **kwargs):
            url = args[1]
            folder = os.path.join(os.getcwd(), 'test_data')
            name = hashlib.md5(url.encode()).hexdigest()
                
            name = name.replace('/','-') + '.html'
            destination = os.path.join(folder, name)
            # print(destination)
            if not os.path.exists(destination):
                return await func(*args, **kwargs)
            async with aiofiles.open(destination, mode='r') as f:
                data = await f.read()
            return data
        return inner_wraper
    return outer_wraper






