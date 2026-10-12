from urllib.request import urlopen
from urllib.error import HTTPError, URLError


class http_validator:
    def __init__(self, config):
        self.config = config

    def check_status(self, type):
        port = self.config["port"]
        if type == "html":
            url = f"http://127.0.0.1:{port}/index.html"
        elif type == "flask":
            check_point = self.config.get("check_point", "/")
            if not isinstance(check_point, str) or not check_point.startswith("/"):
                raise ValueError("check_point 應為以 / 開頭的路徑")
            url = f"http://127.0.0.1:{port}{check_point}"
        else:
            raise ValueError(f"不支援的專案類型：{type}")

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
