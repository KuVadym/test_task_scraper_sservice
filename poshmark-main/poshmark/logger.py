import logging
from re import I
# from tkinter import N
from config import Config
from enum import Enum



class Loger:
    def __init__(self, log_file_name: str, logger_name: str) -> None:
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(Config.LOGGING_LEVEL)
        if not log_file_name.endswith('.log'):
            log_file_name += '.log'
        
        file_handler = logging.FileHandler(f'{log_file_name}', encoding='utf-8')
        file_handler.setLevel(Config.LOGGING_LEVEL)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self._logger.addHandler(file_handler)
    
    
    @property
    def get_logger(self):
        return self._logger
