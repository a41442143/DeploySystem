class multiple_service:
    def __init__(self,config,docker_service,count=None):
        self.config = config
        self.project_name = config["name"]
        if count != None:
            self.names = self.generate_name(count)
        else:
            self.names = []
        self.docker_service = docker_service


    def generate_name(self, count):
        return [f"{self.project_name}_site_{i}" for i in range(count)]

    def generate_instances(self):
        return self.docker_service.docker_multiple_run(self.names)

    def remove_instances(self):
        reports = self.docker_service.check_record()
        prefix = f"{self.project_name}_site_"
        names = [name for name in reports if name.startswith(prefix) and name[len(prefix):].isdigit()]
        if not names:
            raise ValueError(f"找不到專案 {self.project_name} 的受管理實例")

        results = {}
        for name in names:
            report = reports[name]
            if not isinstance(report, dict):
                results[name] = f"容器紀錄檢查未通過：{report}"
                continue

            if report["actual"]["status"] == "running":
                stop_error = self.docker_service.docker_stop(name)
                if stop_error is not None:
                    results[name] = stop_error
                    continue
            results[name] = self.docker_service.docker_remove(name)
        return results
