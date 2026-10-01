import argparse
import sys
class cli_parser:
    def __init__(self):
        self.parser = self.build_parser()
    def build_parser(self) ->argparse.ArgumentParser:
        system_parser = argparse.ArgumentParser(
            description="DeploySystem: 本機自動化部署與驗證工具，以下為說明"
        )
        
        self.subparsers = system_parser.add_subparsers(
            dest= "command",
            required= True
        )
        self.subparsers.add_parser(
            "test",
            help = "執行測試"
        )
        self.deploy_parser = self.subparsers.add_parser(
            "deploy",
            help = "部屬專案，請務必給定設定檔路徑"
        )
        self.deploy_parser.add_argument(
                "config_path",
                type=str,
                help="專案設定檔路徑(json)",
        )
        self.status_parser = self.subparsers.add_parser(
            "status",
            help = "顯示專案部屬狀況"
        )
        self.logs_parser = self.subparsers.add_parser(
            "logs",
            help = "顯示網站運行狀況"
        )
        
        self.stop_parser = self.subparsers.add_parser(
            "stop",
            help = "停止指定專案的運行"
        )
        return system_parser
    def parse(self,argv=None):
        return self.parser.parse_args(argv)
    
def main(argv = None):
    parser = cli_parser()
    args = parser.parse(argv)

    if args.command == "deploy":
        print("this is deploy command test , deploy 的功能尚未實作完成")
    elif args.command == "test":
        print("this is test command test , test 的功能尚未實作完成")
    elif args.command == "logs":
        print("this is logs command test , logs 的功能尚未實作完成")
    elif args.command == "status":
        print("this is status command test , status 的功能尚未實作完成")
    elif args.command == "stop":
        print("this is stop command test , stop 的功能尚未實作完成")



# 避免其他檔案引用時出現錯誤，所以這樣寫python在直接執行該程式時會將__name__設定為__mian__
# ，被引用時則__name__會被設為cli這個名稱
if __name__ == "__main__":
    main()