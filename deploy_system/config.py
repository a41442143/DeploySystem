from pathlib import Path
import json
from config_validator import config_validator

#self.config存放的是config檔讀取後用python的dict形式儲存的資料
class Config:

    def __init__(self,config_path):
        config_path = Path(config_path).resolve()
        if not config_path.exists():
            raise ValueError("file is not exist or 檔案名稱不符合規範")
        self.config_path = config_path
        self.load_json()
    def load_json(self):
        with open(self.config_path , mode = "r" , encoding="utf-8") as f:
            self.config = json.load(f)
        if not isinstance(self.config,dict):
            raise TypeError("config的格式錯誤，最外層資料應為dict")
        self.config_validator = config_validator(self.config)