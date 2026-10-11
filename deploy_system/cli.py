import argparse
from .service.docker.docker_services import docker_services
import sys
from .process_runner import process_runner 
from pathlib import Path
from .config import Config
class cli_parser:
    def __init__(self):
        self.parser = self.build_parser()
    def set_project_path(self,project_path):
        self.process_runner = process_runner()
        self.docker_sevice = docker_services(self.process_runner,project_path)
    def build_parser(self) ->argparse.ArgumentParser:
        system_parser = argparse.ArgumentParser(description="DeploySystem: 本機自動化部署與驗證工具，以下為說明")
        
        self.subparsers = system_parser.add_subparsers(dest= "command",required= True)

        common = argparse.ArgumentParser(add_help=False)
        common.add_argument("config_path", type=Path, help="專案設定檔路徑")

        for command in ("deploy", "test", "logs", "stop", "remove", "status", "start"):
            self.subparsers.add_parser(command, parents=[common])




        return system_parser
    def parse(self,argv=None):
        return self.parser.parse_args(argv)
    
def main(argv=None) -> int:
    parser = cli_parser()
    args = parser.parse(argv)

    if args.command == "test":
        print("HTTP 驗證尚未實作，test 指令暫時無法使用")
        return 2

    try:
        config = Config(args.config_path).config
        parser.set_project_path(config)
        service = parser.docker_sevice

        if args.command == "deploy":
            container_id = service.docker_run(config["name"], config["port"])
            if not container_id:
                print("部署失敗")
                return 1
            print(f"Docker 已建立容器：{container_id.strip()}")
        elif args.command == "status":
            service.docker_status()  # 服務函式目前已自行輸出清單。
        elif args.command == "start":
            result = service.docker_start(config["name"])
            if result is not None:
                print(result)
        elif args.command == "stop":
            result = service.docker_stop(config["name"])
            if isinstance(result, str):
                print(result)
                return 1
        elif args.command == "remove":
            result = service.docker_remove(config["name"])
            if isinstance(result, str):
                print(result)
                return 1
        elif args.command == "logs":
            result = service.docker_logs(config["name"])
            if isinstance(result, str):
                print(result)
                return 1
    except (OSError, ValueError, TypeError, RuntimeError, KeyError) as error:
        print(f"操作失敗：{error}")
        return 1

    return 0



# 避免其他檔案引用時出現錯誤，所以這樣寫python在直接執行該程式時會將__name__設定為__mian__
# ，被引用時則__name__會被設為cli這個名稱
# 用raise SystemExit，之後更新discord遠端操作功能時可能會用到
if __name__ == "__main__":
    raise SystemExit(main())
