from urllib.request import urlopen
from urllib.error import HTTPError, URLError


class http_validator:
    def __init__(self, config):
        self.config = config

    def check_status(self, type):
        url = self._build_url(type, self.config["port"])
        return self._check_url(url)

    def check_multiple_status(self, instances):
        if not isinstance(instances, dict) or not instances:
            raise ValueError("多實例驗證需要非空的容器資訊")

        urls = {}
        for name, record in instances.items():
            if not isinstance(record, dict) or "port" not in record:
                raise ValueError(f"容器 {name} 缺少實際主機 Port")
            urls[name] = self._build_url(self.config["type"], record["port"])

        results = {}
        for name, url in urls.items():
            print(f"正在驗證 {name}：{url}")
            results[name] = self._check_url(url)
        return results

    def _build_url(self, project_type, port):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("主機 Port 應為 1 到 65535 的整數")
        if project_type == "html":
            return f"http://127.0.0.1:{port}/index.html"
        elif project_type == "flask":
            check_point = self.config.get("check_point", "/")
            if not isinstance(check_point, str) or not check_point.startswith("/"):
                raise ValueError("check_point 應為以 / 開頭的路徑")
            return f"http://127.0.0.1:{port}{check_point}"
        else:
            raise ValueError(f"不支援的專案類型：{project_type}")

    def _check_url(self, url):
        try:
            with urlopen(url, timeout=10) as response:
                status = response.status
        except HTTPError as error:
            status = error.code
        except (URLError, TimeoutError) as error:
            print(f"無法連線至網站：{error}")
            return 5

        if status == 200:
            print("網站啟動成功")
            return 0
        if status == 404:
            print("找不到頁面，網站佈署失敗")
            return 2
        if status == 500:
            print("網站錯誤無法正確啟動")
            return 3
        print(f"網站回傳非預期狀態碼：{status}")
        return 4
