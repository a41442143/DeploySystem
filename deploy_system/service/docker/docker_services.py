from pathlib import Path
import hashlib
import json
from ...process_runner import process_runner
from .record_store import RecordStore
from .container_comparator import ContainerComparator
from ...config import Config
class docker_services:

    def __init__(self,process_runner:process_runner,config):
        self.config = config
        project_path = config["path"]
        self.type = config["type"]
        self.project_path = project_path
        self.process_runner = process_runner
        self.client = DockerClient(self.process_runner)
        self.record_store = RecordStore(Path(__file__).with_name("server_record.json"))
        self.comparator = ContainerComparator()
        self.dockerClient = DockerClient(self.process_runner)
    def check_project_dir(self):
        type = self.type
        if not self.project_path.is_dir():
            raise TypeError("project path should be the path of the project you want to employ")
        if type == "html":
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
        else:
            required = ("app.py", "requirements.txt", ".dockerignore")
            for filename in required:
                if not (self.project_path / filename).is_file():
                    raise ValueError(f"Flask 專案缺少必要檔案：{filename}")

            dockerfile = self.project_path / "Dockerfile"
            #check檔案是否存在，之後根據情況決定是否預設建立docekr file
            if dockerfile.exists():
                if not dockerfile.is_file():
                    raise ValueError("Dockerfile 必須是檔案")
            else:
                container_port = self.config.get("container_port", 8000)
                content = (
                    "FROM python:3.12-slim\n"
                    "WORKDIR /app\n"
                    "COPY requirements.txt .\n"
                    "RUN pip install --no-cache-dir -r requirements.txt\n"
                    "COPY . .\n"
                    f"EXPOSE {container_port}\n"
                    'CMD ["python", "app.py"]\n'
                )
                with dockerfile.open("x", encoding="utf-8") as file:
                    file.write(content)
                print(f"已建立預設 Dockerfile：{dockerfile}")
    def check_dir(self,FORBID_LIST,target:Path):
        if target.name in FORBID_LIST:
            raise ValueError(f'這是高敏資料夾，上傳的專案內不該包含此資料夾，路徑為{target}')
        else:
            for child_target in target.iterdir():
                if child_target.is_dir():
                    self.check_dir(FORBID_LIST,child_target)
                elif child_target.name ==".env":
                    raise ValueError(f'這是高敏檔案，上傳的專案內不該包含此檔案，路徑為{child_target}')

    def docker_build(self):
        if self.type != "flask":
            raise ValueError("docker_build 目前只支援 Flask 專案")
        self.check_project_dir()
        dockerfile = self.project_path / "Dockerfile"
        if not dockerfile.is_file():
            raise ValueError("找不到 Dockerfile，請先完成預設 Dockerfile 的補檔處理")

        identity = f"{self.config['name']}|{self.project_path.resolve()}"
        suffix = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
        image_tag = f"deploysystem-flask-{suffix}:latest"
        self.dockerClient._run([
            "docker", "build", "--tag", image_tag,
            "--file", str(dockerfile), str(self.project_path),
        ])
        return image_tag


    def docker_multiple_run(self, names):
        report = self.check_record()
        results = {}
        image_tag = None
        for name in names:
            if name in report:
                print(f"容器資訊檢查完畢，你要部屬的容器當前狀態為:{report[name]}")
                if not isinstance(report[name], dict):
                    print(f"容器紀錄檢查未通過，無法啟動：{report[name]}")
                    return None
                print("該容器已存在，所以改為使用start指令")
                start_error = self.docker_start(name)
                if start_error is not None:
                    print(f"啟動既有容器失敗：{start_error}")
                    return None
                record = self.record_store.load()[name]
                detail = self.dockerClient.inspect(record["id"])
                actual = self.handle_detail(detail)
                if record["port"] != actual["port"]:
                    self.record_store.update_fields(name, {"port": actual["port"]})
                results[name] = actual
                continue

            print("report中尚不存在該容器，即將建立並部屬該容器")
            if self.type == "html":
                try:
                    self.check_project_dir()
                    args = ["docker", "run", "-d", "--name", name,
                            "--label", "deploysystem.owner=DeploySystem",
                            "--publish", "127.0.0.1::80",
                            "--mount",
                            f"type=bind,source={self.project_path.resolve()},target=/usr/share/nginx/html,readonly",
                            "nginx:alpine"]
                    result = self.dockerClient._run(args)
                except Exception as error:
                    print(f"HTML 容器部署失敗：{error}")
                    return None
            elif self.type == "flask":
                try:
                    if image_tag is None:
                        image_tag = self.docker_build()
                    container_port = self.config.get("container_port", 8000)
                    args = [
                        "docker", "run", "-d", "--name", name,
                        "--label", "deploysystem.owner=DeploySystem",
                        "--label", f"deploysystem.project_path={self.project_path.resolve()}",
                        "--publish", f"127.0.0.1::{container_port}",
                        image_tag,
                    ]
                    result = self.dockerClient._run(args)
                except Exception as error:
                    print(f"Flask 容器建置或啟動失敗：{error}")
                    return None
            else:
                raise ValueError(f"不支援的專案類型：{self.type}")

            detail = self.dockerClient.inspect(result.strip())
            actual = self.handle_detail(detail)
            self.record_store.add_fields(name, actual)
            results[name] = actual
        return results

    def docker_run(self,name,port,label=None):
        report = self.check_record()
        if name in report.keys():
            print(f'容器資訊檢查完畢，你要部屬的容器當前狀態為:{report[name]}')
            if isinstance(report[name],dict):
                print("該容器已存在，所以改為使用start指令")
                result = self.docker_start(name)
                if result is not None:
                    print(f"啟動既有容器失敗：{result}")
                    return None
                return "該容器已存在，啟動檢查完成，可直接使用該名稱操作容器"
            else:
                print(f"容器紀錄檢查未通過，無法啟動：{report[name]}")
                return None
        else:
            print("report中尚不存在該容器，即將建立並部屬該容器")
        if self.type == "html":
            try:
                self.check_project_dir()
            except Exception as e:
                print(f'處理過程出現錯誤，執行失敗: {e}')
                return None
            else:
                args = ["docker", "run", "-d", "--name",name,
                        "--label", "deploysystem.owner=DeploySystem",
                        "--publish", f"127.0.0.1:{port}:80",
                        "--mount",
                        f"type=bind,source={self.project_path.resolve()},target=/usr/share/nginx/html,readonly",
                        "nginx:alpine"
                        ]
                try:
                    result = self.dockerClient._run(args)
                except Exception as e:
                    print(e)
                    return None
                detail = self.dockerClient.inspect(result.strip())
                update_data = self.handle_detail(detail)
                self.record_store.add_fields(name,update_data)
                return result
        elif self.type == "flask":
            try:
                image_tag = self.docker_build()
                container_port = self.config.get("container_port", 8000)
                args = [
                    "docker", "run", "-d", "--name", name,
                    "--label", "deploysystem.owner=DeploySystem",
                    "--label", f"deploysystem.project_path={self.project_path.resolve()}",
                    "--publish", f"127.0.0.1:{port}:{container_port}",
                    image_tag,
                ]
                result = self.dockerClient._run(args)
            except Exception as error:
                print(f"Flask 容器建置或啟動失敗：{error}")
                return None

            detail = self.dockerClient.inspect(result.strip())
            update_data = self.handle_detail(detail)
            self.record_store.add_fields(name, update_data)
            return result

        
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
                ans = input("紀錄應為dict格式，發現格式錯誤請問是否刪除該紀錄?(想刪除請輸入Y，否則皆視為否)")
                if ans == "Y":
                    self.record_store.delete_record(name=name)
                    reports[name] = ["資料格式錯誤，已被刪除"]
                reports[name] = ["資料格式錯誤，但目前被保留"]
            elif name not in containers:
                print(f'目前找不到名稱為{name}的容器')
                ans = input("是否刪除該紀錄?(想刪除請輸入Y，否則皆視為否)")
                if ans == "Y":
                    self.record_store.delete_record(name=name)
                    reports[name] = ["Docker 中找不到同名容器，紀錄已被刪除"]
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
                    else:
                        raise ValueError("systemError")
        return reports

    def show_record(self):
        records = self.record_store.load()
        i = 0
        for key,value in records:
            i += 1
            print(f"cotainer{i}. {key} : {value}")


    def handle_report(self,report):
        differences = set(report["differences"])
        if not differences:
            return 0

        if "label" in differences:
            print("非本系統管理的容器，停止操作")
            raise ValueError("systemError")
        elif "name" in differences:
            if "id" not in differences:
                raise ValueError("nameError")
        elif "id" in differences:
            raise ValueError("the container is changed")
        elif "port" in differences or "project_path" in differences:
            print("停止操作，請聯繫系統管理者，容器追蹤檔的寫入出現問題")
            raise ValueError("systemError")
        elif differences == {"status"}:
            raise ValueError("Status Error")

            
    #將inspect出來的容器資料轉成dict並回傳
    def handle_detail(self,detail):
        container_port = self.config.get("container_port", 8000) if self.type == "flask" else 80
        actual = self.comparator.extract_actual(detail, self.type, container_port)
        if actual["label"] != "DeploySystem":
            raise ValueError("非本系統管理的容器，不可更新紀錄")
        if (
            not actual["id"]
            or actual["status"] not in {"running", "exited"}
            or actual["port"] is None
            or actual["project_path"] is None
        ):
            raise ValueError("容器資訊不完整，不可更新紀錄")
        record = {
            key: actual[key]
            for key in ("id", "label", "status", "port", "project_path")
        }
        record["type"] = self.type
        if self.type == "flask":
            record["container_port"] = container_port
        return record

    def docker_status(self):
        info = self.dockerClient.ps_all()
        print(info)
        return info

    def check_before_use_docker(self,container_name):
        reports = self.check_record()
        if container_name in reports.keys():
            if isinstance(reports[container_name],dict):
                return True
        return False
    def docker_start(self,container_name):
        if self.check_before_use_docker(container_name):
            record = self.record_store.load()
            container_id = record[container_name]["id"]
            if record[container_name]["status"] == "exited" or record[container_name]["status"] == "created":
                args = ["docker", "start", container_id]
                self.dockerClient._run(args)
                print(f"容器 {container_name} 已啟動")
                return None
            if record[container_name]["status"] == "running":
                print(f"容器 {container_name} 已在執行中")
                return None
            return f"容器 {container_name} 目前狀態為 {record[container_name]['status']}，無法直接啟動"
        return f"找不到可操作的受管理容器：{container_name}"
            
    def docker_stop(self,container_name):
        if self.check_before_use_docker(container_name):
            record = self.record_store.load()
            container_id = record[container_name]["id"]
            args = ["docker", "stop", "--timeout", "15", container_id]
            try:
                result = self.dockerClient._run(args)
                print(f"停止指令執行結果如下{result}")
                return None
            except Exception as e:
                return f"Error happen when execute command , Error : {str(e)}"
        return f"找不到可操作的受管理容器：{container_name}"

    def docker_remove(self,container_name):
        if not self.check_before_use_docker(container_name):
            return f"找不到可刪除的受管理容器：{container_name}"

        record = self.record_store.load()
        container_id = record[container_name]["id"]
        try:
            detail = self.dockerClient.inspect(container_id)
            actual = self.comparator.extract_actual(detail)
            if actual["id"] != container_id or actual["label"] != "DeploySystem":
                return "容器 ID 或管理標籤不符，停止刪除"
            if detail["State"]["Status"] not in {"created", "exited"}:
                return f"容器 {container_name} 尚未停止，請先執行 stop"
            self.dockerClient._run(["docker", "rm", container_id])
        except (OSError, ValueError, TypeError, RuntimeError, KeyError) as error:
            return f"刪除容器失敗：{error}"

        try:
            self.record_store.delete_record(container_name)
            if container_name in self.record_store.load():
                raise RuntimeError("紀錄仍存在")
        except (OSError, ValueError, TypeError, RuntimeError, KeyError) as error:
            return f"容器已刪除，但系統紀錄清除失敗：{error}"

        print(f"容器 {container_name} 與系統紀錄已刪除")
        return None

    def docker_logs(self,container_name):
        if self.check_before_use_docker(container_name):
            record = self.record_store.load()
            container_id = record[container_name]["id"]
            args = ["docker", "logs", "--tail", "100", "--timestamps", container_id]
            try:
                result = self.dockerClient._run(args)
                if result.strip():
                    print(result)
                else:
                    print(f"容器 {container_name} 沒有可顯示的標準輸出日誌")
                return None
            except Exception as e:
                return f"Error happen when execute command , Error : {str(e)}"
        return f"找不到可操作的受管理容器：{container_name}"



class DockerClient:
    def __init__(self, runner: process_runner):
        self.runner = runner

    #執行docker指令
    def _run(self, args: list[str]) -> str:
        timeout = 600 if args[:2] == ["docker", "build"] else 30
        result = self.runner.run(args, timeout=timeout)
        #運行docker指令順便做基礎檢查
        if result.result != 0:
            if result.result is None :
                detail = (f"工具錯誤碼 {result.error_code}")
            else:
                detail = (f"退出碼 {result.result}")
            raise RuntimeError(f"Docker 查詢失敗（{detail}）：{result.stderr}")

        return result.stdout or ""

    #執行docker ps -a
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

    #執行docker inspect指令
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
