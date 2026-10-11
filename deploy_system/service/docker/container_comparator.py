from pathlib import Path


class ContainerComparator:
    LABEL_KEY = "deploysystem.owner"
    PROJECT_PATH_LABEL = "deploysystem.project_path"
    SITE_DESTINATION = "/usr/share/nginx/html"

    def extract_actual(self, detail, project_type="html", container_port=None):
        if project_type not in {"html", "flask"}:
            raise ValueError(f"不支援的專案類型：{project_type}")
        if project_type == "html":
            container_port = 80
        elif container_port is None:
            container_port = 8000
        if type(container_port) is not int or not 1 <= container_port <= 65535:
            raise ValueError("container_port 應為 1 到 65535 的整數")
        labels = (detail.get("Config") or {}).get("Labels") or {}
        actual_name = detail.get("Name", "").removeprefix("/")
        actual_id = detail.get("Id")
        actual_label = labels.get(self.LABEL_KEY)
        actual_status = (detail.get("State") or {}).get("Status")
        bindings = (
            (detail.get("HostConfig") or {}).get("PortBindings") or {}
        ).get(f"{container_port}/tcp") or []

        actual_port = None
        if len(bindings) == 1:
            host_port = bindings[0].get("HostPort")
            if host_port is not None and str(host_port).isdigit():
                actual_port = int(host_port)

        if project_type == "html":
            site_mounts = [
                mount
                for mount in (detail.get("Mounts") or [])
                if mount.get("Destination") == self.SITE_DESTINATION
            ]
            actual_path = None
            if len(site_mounts) == 1 and site_mounts[0].get("Type") == "bind":
                actual_path = site_mounts[0].get("Source")
        else:
            actual_path = labels.get(self.PROJECT_PATH_LABEL)

        return {
            "name": actual_name,
            "id": actual_id,
            "label": actual_label,
            "status": actual_status,
            "port": actual_port,
            "project_path": actual_path,
        }

    def compare(self, name, record, detail):
        actual = self.extract_actual(
            detail,
            record.get("type", "html"),
            record.get("container_port"),
        )
        differences = []

        name_matches = actual["name"] == name and record.get("name") == name
        id_matches = actual["id"] is not None and actual["id"] == record.get("id")
        if not name_matches and not id_matches:
            raise ValueError("容器名稱與 ID 均不符，無法視為同一容器")

        if not name_matches:
            differences.append("name")
        if not id_matches:
            differences.append("id")
        if record.get("label") != "DeploySystem" or actual["label"] != "DeploySystem":
            differences.append("label")
        if record.get("status") != actual["status"]:
            differences.append("status")
        if actual["port"] is None or str(actual["port"]) != str(record.get("port")):
            differences.append("port")

        recorded_path = record.get("project_path")
        if (
            actual["project_path"] is None
            or recorded_path is None
            or Path(actual["project_path"]).resolve() != Path(recorded_path).resolve()
        ):
            differences.append("project_path")

        return {
            "differences": differences,
            "actual": actual,
        }
