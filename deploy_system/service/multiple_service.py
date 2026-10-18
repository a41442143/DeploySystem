class multiple_service:
    def __init__(self,config,count,docker_service):
        self.config = config
        self.project_name = config["name"]
        self.names = self.generate_name(count)
        self.docker_service = docker_service

    def generate_name(self,count):
        return [f"{self.project_name}_site-{i}" for i in range(count)]

    def generate_instances(self):
        return self.docker_service.docker_multiple_run(self.names)
