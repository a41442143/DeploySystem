from pathlib import Path
class config_validator:
    def __init__(self , config , config_parent_path):
        self.config = config
        self.validate()
        self.validate_name()
        self.validate_path(config_parent_path)
        self.validate_port()
        self.validate_type()
        self.validate_time_out()
    def validate(self):
        if not self.config:
            raise ValueError("config is empty , and it should not be empty")
        required_datas = ["name","type","path","port"]
        for required_data in required_datas:
            if required_data not in self.config.keys():
                raise ValueError(f'{required_data} 該欄位為必填')
            if not self.config[required_data]:
                raise ValueError(f'this field {required_data} should not be empty')
    
    def validate_port(self):
        if isinstance(self.config["port"],int):
            if self.config["port"] > 65535 or self.config["port"] < 1:
                raise ValueError("選取的port範圍不合法")
        else:
            raise TypeError("port應為數字")
    
    def validate_name(self):
        if not isinstance(self.config["name"] , str):
            raise TypeError("該欄位應為str")
    
    
    def validate_type(self):
        valid_type = ["flask","html"]
        if not isinstance(self.config["type"] , str):
            raise TypeError("該欄位應為str")
        if self.config["type"] not in valid_type:
            raise ValueError("invalid type,please check your config")
    
    
    #path欄位內存放的應為網站的專案路徑，故檢查該資料夾是否存在及是否為資料夾
    def validate_path(self,config_parent_path):
        temp_project_path = Path(self.config["path"])
        if not isinstance(self.config["path"] , str):
            raise TypeError("該欄位應為str")
        if not temp_project_path.is_absolute():
            base_dir = Path(config_parent_path)
            rel_path = Path(self.config["path"])
            self.config["path"] = (base_dir/rel_path).resolve()
        else:
            self.config["path"] = temp_project_path
        if not self.config["path"].exists():
            raise ValueError("該路徑錯誤，找不到目標資料夾")
        if not self.config["path"].is_dir():
            raise TypeError("傳入路徑應為資料夾路徑")
        if len(list(self.config["path"].iterdir())) == 0:
            raise ValueError("目標資料夾底下不應為空")
        

    def validate_time_out(self):
        if "time_out" not in self.config.keys():
            self.config["time_out"] = 500       #預設timeout 5分鐘
        else:
            if not self.config["time_out"]:
                self.config["time_out"] = 500       #預設timeout 5分鐘
            else:
                if not isinstance(self.config["time_out"] , int):
                    self.config["time_out"] = 500
                    print("time_out不符合格是規範已經將其設為預設值")
                