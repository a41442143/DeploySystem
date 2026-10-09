from pathlib import Path


class ContainerComparator:
    LABEL_KEY = "deploysystem.owner"
    SITE_DESTINATION = "/usr/share/nginx/html"

    def extract_actual(self, detail):
        labels = (detail.get("Config") or {}).get("Labels") or {}
        actual_name = detail.get("Name", "").removeprefix("/")
        actual_id = detail.get("Id")
        actual_label = labels.get(self.LABEL_KEY)
        actual_status = (detail.get("State") or {}).get("Status")
        bindings = (
            (detail.get("HostConfig") or {}).get("PortBindings") or {}
        ).get("80/tcp") or []

        actual_port = None
        if len(bindings) == 1:
            host_port = bindings[0].get("HostPort")
            if host_port is not None and str(host_port).isdigit():
                actual_port = int(host_port)

        site_mounts = [
            mount
            for mount in (detail.get("Mounts") or [])
            if mount.get("Destination") == self.SITE_DESTINATION
        ]

        actual_path = None
        if len(site_mounts) == 1 and site_mounts[0].get("Type") == "bind":
            actual_path = site_mounts[0].get("Source")

        return {
            "name": actual_name,
            "id": actual_id,
            "label": actual_label,
            "status": actual_status,
            "port": actual_port,
            "project_path": actual_path,
        }

    def compare(self, name, record, detail):
        actual = self.extract_actual(detail)
        differences = []

        if actual["name"] != name or record.get("name") != name:
            differences.append("name")
        if actual["id"] != record.get("id"):
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
