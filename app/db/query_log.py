from fileinput import filename
import logging

#file 
from pathlib import Path
import sys
import os

fmt = logging.Formatter(
    fmt="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# log setup here

class FileLog():
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type
        
    def create_file(self):
        file_name = self.name + '.' + self.type
        if not os.path.isfile(file_name):
            file = open(r'db/' + file_name ,'a+') 
        
    # @classmethod
    # def open_file(cls, file_name: str):
    #     open(file_name)

log_file = FileLog('log', 'txt')
log_file.create_file()
