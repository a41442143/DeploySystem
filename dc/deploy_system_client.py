from ..deploy_system.process_runner import process_runner
class deploy_system_client:
    def __init__(self):
        self.process_runner = process_runner()
    
    async def deploy(self,project_config_path):
        commannd = ["python","-m","deploy_system.cli","deploy",f"{project_config_path}"]
        try:
            result = self.process_runner.run(commannd,timeout=30)
            print(result.stdout)
        except (OSError, ValueError, TypeError, RuntimeError, KeyError) as error:
            print(f"操作失敗：{error}")
            print(error)