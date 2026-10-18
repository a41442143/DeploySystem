import argparse
from .service.docker.docker_services import docker_services
import sys
from .process_runner import process_runner 
from pathlib import Path
from .config import Config
from .service.http_status_validator import http_validator
from .service.multiple_service import multiple_service
import time
class cli_parser:
    def __init__(self):
        self.parser = self.build_parser()

    def set_config(self,config):
        self.process_runner = process_runner()
        self.http_validator = http_validator(config)
        self.docker_sevice = docker_services(self.process_runner,config)
    def build_parser(self) ->argparse.ArgumentParser:
        system_parser = argparse.ArgumentParser(description="DeploySystem: 本機自動化部署與驗證工具，以下為說明")
        
        self.subparsers = system_parser.add_subparsers(dest= "command",required= True)

        common = argparse.ArgumentParser(add_help=False)
        common.add_argument("config_path", type=Path, help="專案設定檔路徑")

        for command in ("deploy", "test", "logs", "stop", "remove", "status", "start"):
            self.subparsers.add_parser(command, parents=[common])
        multiple_parser = self.subparsers.add_parser("multiple-deploy", parents=[common])
        multiple_parser.add_argument("count", type=int, help="要部署的實例數量")
        self.subparsers.add_parser("multiple-remove", parents=[common])



        return system_parser
    def parse(self,argv=None):
        return self.parser.parse_args(argv)

    def test(self, project_type):
        result = self.http_validator.check_status(project_type)
        return result
    
def main(argv=None) -> int:
    parser = cli_parser()
    args = parser.parse(argv)
    try:
        if args.command not in {"multiple-deploy", "multiple-remove"}:
            config = Config(args.config_path).config
        else:
            config = Config(args.config_path,True).config
        parser.set_config(config)
        service = parser.docker_sevice
        if args.command == "test":
            return parser.test(config["type"])
        if args.command == "deploy":
            container_id = service.docker_run(config["name"], config["port"])
            if not container_id:
                print("部署失敗")
                return 1
            result = parser.test(config["type"])
            print(f"部署操作完成：{container_id.strip()}")
            return result
        elif args.command == "status":
            service.docker_status()  # 服務函式目前已自行輸出清單。
        elif args.command == "start":
            result = service.docker_start(config["name"])
            if isinstance(result, str):
                print(result)
                return 1
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
        elif args.command == "multiple-deploy":
            if args.count < 1:
                raise ValueError("實例數量不應小於1")
            deployment = multiple_service(config, service, args.count)
            instances = deployment.generate_instances()
            if not instances:
                print("多實例部署失敗")
                return 1
            checks = parser.http_validator.check_multiple_status(instances)
            for name, record in instances.items():
                print(f"{name}：http://127.0.0.1:{record['port']}/")
            for status in checks.values():
                if status != 0:
                    return 1
            return 0
        elif args.command == "multiple-remove":
            deployment = multiple_service(config, service)
            results = deployment.remove_instances()
            failed = False
            for name, error in results.items():
                if error is not None:
                    print(f"{name} 刪除失敗：{error}")
                    failed = True
            if failed:
                return 1
            return 0
    except (OSError, ValueError, TypeError, RuntimeError, KeyError) as error:
        print(f"操作失敗：{error}")
        return 1

    return 0



# 避免其他檔案引用時出現錯誤，所以這樣寫python在直接執行該程式時會將__name__設定為__mian__
# ，被引用時則__name__會被設為cli這個名稱
# 用raise SystemExit，之後更新discord遠端操作功能時可能會用到
if __name__ == "__main__":
    raise SystemExit(main())
