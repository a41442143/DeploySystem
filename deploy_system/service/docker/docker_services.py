from pathlib import Path
import json
from ...process_runner import process_runner
from .record_store import RecordStore
from .container_comparator import ContainerComparator

class docker_services:
    def __init__(self,process_runner:process_runner,project_path:Path):
        self.project_path = project_path
        self.process_runner = process_runner
        self.client = DockerClient(self.process_runner)
        self.record_store = RecordStore(Path(__file__).with_name("server_record.json"))
        self.comparator = ContainerComparator()
        
    def check_project_dir(self):
        if not self.project_path.is_dir():
            raise TypeError("project path should be the path of the project you want to employ")
        FORBID_LIST = [".env",".git",".vscode"]
        for target in self.project_path.iterdir():
            if target.name == FORBID_LIST[0]:
                raise ValueError(f'這是高敏檔案，上傳的專案內不該包含此資料夾，路徑為{target}')
            if target.is_dir():
                self.check_dir(FORBID_LIST , target)
        if not Path(self.project_path/"index.html").exists():
            raise ValueError("根目錄底下應該要包含Index.html")
        else:
            if Path(self.project_path/"index.html").is_dir():
                raise TypeError("index.hmtl應為檔案而非資料夾")
            
    def check_dir(self,FORBID_LIST,target:Path):
        if target.name in FORBID_LIST:
            raise ValueError(f'這是高敏資料夾，上傳的專案內不該包含此資料夾，路徑為{target}')
        else:
            for child_target in target.iterdir():
                if child_target.is_dir():
                    self.check_dir(FORBID_LIST,child_target)
                elif child_target.name ==".env":
                    raise ValueError(f'這是高敏檔案，上傳的專案內不該包含此檔案，路徑為{child_target}')
    def docker_run(self):
        pass

    def check_record(self) -> dict[str, object]:
        records = self.record_store.load()
        listed = self.client.ps_all()

        #優先依名稱找；名稱改變時，仍可用紀錄中的完整 ID 找到同一容器。
        listed_ids = set(listed.values())
        containers = {}
        for name, record in records.items():
            if name in listed:
                containers[name] = listed[name]
            elif isinstance(record, dict) and record.get("id") in listed_ids:
                containers[name] = record["id"]
        
        inspected = {}
        inspect_errors = {}
        #挑出被追蹤中的容器後取得Docker中這些容器的完整資料準備進行檢查
        for name, container_id in containers.items():
            try:
                inspected[name] = self.client.inspect(container_id)
            except (RuntimeError, ValueError) as error:
                inspect_errors[name] = str(error)

        #開始比對
        reports = {}
        for name, record in records.items():
            if not isinstance(record, dict):
                reports[name] = ["紀錄格式錯誤：每筆紀錄必須是 JSON 物件"]
            elif name not in containers:
                reports[name] = ["Docker 中找不到同名容器"]
            elif name in inspect_errors:
                reports[name] = [
                    f"無法取得容器詳細資訊：{inspect_errors[name]}"
                ]
            else:
                reports[name] = self.comparator.compare(
                    name, record, inspected[name]
                )
                try:
                    self.handle_report(reports[name])
                except ValueError as e:
                    if str(e) == "Status Error":
                        self.record_store.update_fields(
                            name=name,
                            updates={"status": reports[name]["actual"]["status"]},
                        )
                    elif str(e) == "the container is changed":
                        print(f"同名容器的資訊已改變：{reports[name]['actual']}")
                        ans = input("你使用的名稱ID已被改過，可能是被重新run過，你是否要將新容器的資訊覆寫?(Y/N)")
                        if ans == "Y":
                            self.record_store.update_fields(name=name,updates=self.handle_detail(inspected[name]))
                        elif ans == "N":
                            print("好的，我們將不做修改")
                        else:
                            print("輸入錯誤，只能輸入Y or N")
                    elif str(e) == "nameError":
                        new_name = reports[name]["actual"]["name"]
                        if new_name == name or new_name in records:
                            print("容器名稱與紀錄不一致，請聯繫系統管理者；不會覆寫其他紀錄")
                            continue
                        ans = input("你尋找的容器的名稱已被修改，你是否要用修改後的名稱覆寫?(Y/N)")
                        if ans == "Y":
                            self.record_store.update_fields(
                                name=new_name,
                                updates=self.handle_detail(inspected[name]),
                                id=record["id"],
                            )
                        elif ans == "N":
                            print("好的，我們將不做修改")
                        else:
                            print("輸入錯誤，只能輸入Y or N")
        return reports
    def handle_report(self,report):
        differences = set(report["differences"])
        if not differences:
            return 0

        if "label" in differences:
            print("非本系統管理的容器，停止操作")
        elif "name" in differences:
            if "id" in differences:
                print("容器名稱及 ID 同時不一致，停止操作")
            else:
                raise ValueError("nameError")
        elif "id" in differences:
            raise ValueError("the container is changed")
        elif "port" in differences or "project_path" in differences:
            print("停止操作，請聯繫系統管理者，容器追蹤檔的寫入出現問題")
        elif differences == {"status"}:
            if report["actual"]["status"] in {"running", "exited"}:
                raise ValueError("Status Error")
            print("容器狀態不是 running 或 exited，停止自動更新")

    def handle_detail(self,detail):
        actual = self.comparator.extract_actual(detail)
        if actual["label"] != "DeploySystem":
            raise ValueError("非本系統管理的容器，不可更新紀錄")
        if (
            not actual["id"]
            or actual["status"] not in {"running", "exited"}
            or actual["port"] is None
            or actual["project_path"] is None
        ):
            raise ValueError("容器資訊不完整，不可更新紀錄")
        return {
            key: actual[key]
            for key in ("id", "label", "status", "port", "project_path")
        }

    def docker_status(self):
        pass






class DockerClient:
    def __init__(self, runner: process_runner):
        self.runner = runner

    def _run(self, args: list[str]) -> str:
        result = self.runner.run(args, timeout=30)
        #運行docker指令順便做基礎檢查
        if result.result != 0:
            if result.result is None :
                detail = (f"工具錯誤碼 {result.error_code}")
            else:
                detail = (f"退出碼 {result.result}")
            raise RuntimeError(f"Docker 查詢失敗（{detail}）：{result.stderr}")

        return result.stdout or ""

    def ps_all(self) -> dict[str, str]:
        output = self._run(["docker", "ps", "-a", "--no-trunc", "--format", "json"])
        containers = {}
        for line in output.splitlines():#逐行讀取回傳的結果，理論上每一行都是一個容器的資訊
            if not line.strip():
                continue
            item = json.loads(line)
            containers[item["Names"]] = item["ID"]
        #整理PS出來的結果並儲存成LIST
        return containers

    def inspect(self, container_id: str) -> dict:
        #inspect負責秀出指定ID的容器的完整資料
        output = self._run(["docker", "inspect", "--type=container", container_id])
        items = json.loads(output)

        if not isinstance(items, list) or len(items) != 1:
            raise ValueError("inspect 未回傳單一容器資料")

        detail = items[0]
        if detail.get("Id") != container_id:
            raise ValueError("inspect 回傳的容器 ID 與查詢目標不同")

        return detail
