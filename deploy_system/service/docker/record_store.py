import json
import tempfile
from pathlib import Path

class RecordStore:
    def __init__(self, path):
        self.path = path

    def load(self):
        with self.path.open("r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, dict):
            raise ValueError("紀錄檔頂層必須是 JSON 物件")
        return records

    
    #儲存已經處理過的record進json
    def save(self,record):
        try:
            temp_file_path = None
            with open(self.path.parent/"temp_record.tmp",mode="w",encoding="utf-8") as temp_file:
                temp_file_path = Path(temp_file.name)
                json.dump(record ,temp_file ,ensure_ascii=False, indent=2 )
                temp_file.flush()
            temp_file_path.replace(self.path)
        except Exception as e:
            print(f'寫入檔案發生錯誤:{e}，請重新嘗試')

    def add_fields(self,name,updates):
        record = self.load()
        if name not in record.keys():
            updates["name"] = name
            record[name] = updates
            self.save(record)

    def update_fields(self, name: str, updates: dict , id =None) -> None:
        allowed_fields = {"id", "label", "status", "port", "project_path"}
        invalid_fields = set(updates) - allowed_fields
        if invalid_fields:
            raise ValueError(f"不允許更新的欄位：{sorted(invalid_fields)}")

        records = self.load()

        if id != None:
            for Name in records.keys():
                if records[Name]["id"] == id:
                    #找出id相同但name不同的容器資料，並將其更新
                    if Name != name:
                        records[name] = records[Name]
                        records[name]["name"] = name
                        del records[Name]
                    break
        records[name].update(updates)
        self.save(records)
            
    def delete_record(self,name):
        records = self.load()
        if name in records:
            del records[name]
            self.save(records)
        else:
            raise ValueError("this name is unknown")
