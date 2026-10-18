# DeploySystem

DeploySystem 是以 Python 撰寫的本機 Docker 網站部署工具。使用者以 JSON 指定專案位置與類型，再透過 CLI 部署靜態網站或 Flask 網站、檢查 HTTP 回應、查看容器狀態及日誌。多實例模式可一次建立數個同專案容器，由 Docker 自動分配各自的主機 Port。

## 執行需求

- Python 3.12。
- 已啟動的 Docker Desktop Linux containers engine，以及可在命令列使用的 docker 指令。
- 從專案根目錄執行下列 CLI 指令。CLI 核心使用 Python 標準函式庫；Flask 專案的套件由其 requirements.txt 在映像檔建置時安裝。

系統紀錄存放於 deploy_system/service/docker/server_record.json。此檔案不納入 Git；第一次使用前，若檔案不存在，請建立檔案並寫入空的 JSON 物件：

~~~json
{}
~~~

紀錄檔保存受管理容器的名稱、ID、狀態、Port 與專案路徑。請保留此檔案，以便後續執行 start、stop、remove 與 multiple-remove。

## 準備網站與設定檔

每個 CLI 子指令都需要一份 JSON 設定檔。path 可以是絕對路徑，也可以是相對於「設定檔所在資料夾」的路徑。建議將個人設定檔放在 project_config/；此資料夾已列入 .gitignore。

靜態網站的資料夾根目錄必須包含 index.html。系統使用 nginx:alpine，將網站資料夾唯讀掛載到容器內的 /usr/share/nginx/html。範例設定檔：

~~~json
{
  "name": "my-static-site",
  "type": "html",
  "path": "../my_static_site",
  "port": 18081
}
~~~

Flask 專案需提供 app.py、requirements.txt 及 .dockerignore。若缺少 Dockerfile，系統會建立預設檔：以 Python 3.12 安裝 requirements.txt，並執行 python app.py；既有 Dockerfile 則會直接使用。Flask 程式須在容器內監聽 0.0.0.0，且監聽 Port 必須與 container_port 一致。範例設定檔：

~~~json
{
  "name": "my-flask-site",
  "type": "flask",
  "path": "../my_flask_site",
  "port": 18082,
  "container_port": 8000,
  "check_point": "/health"
}
~~~

| 欄位 | 用途 |
| --- | --- |
| name | 單實例容器名稱；多實例時作為名稱前綴。 |
| type | html 或 flask。 |
| path | 網站專案資料夾。 |
| port | 單實例使用的主機 Port，必填；多實例部署不使用此值，也可省略。 |
| container_port | Flask 在容器內監聽的 Port，預設 8000。靜態網站固定使用容器內 Port 80。 |
| check_point | Flask 的 HTTP 驗證路徑，預設 /；靜態網站固定驗證 /index.html。 |

請確認設定檔與 Flask 程式的監聽位址、Port 一致。預設 Dockerfile 適合簡單範例；也可以自行提供 Dockerfile 與適當的應用程式伺服器。

## CLI 指令

在專案根目錄執行：

~~~cmd
python -m deploy_system.cli --help
~~~

下表中的 CONFIG.json 請換成自己的設定檔路徑。

| 指令 | 行為 |
| --- | --- |
| deploy CONFIG.json | 部署單一容器；若同名容器已由系統管理，則嘗試啟動既有容器，接著檢查 HTTP 狀態碼。 |
| test CONFIG.json | 向設定檔指定的單實例主機 Port 發出一次 HTTP GET；收到 200 才成功。 |
| status CONFIG.json | 列出 Docker 容器清單；此指令也需要傳入設定檔。 |
| start CONFIG.json | 啟動設定檔 name 指定的受管理容器。 |
| stop CONFIG.json | 停止設定檔 name 指定的受管理容器。 |
| logs CONFIG.json | 顯示該容器最近 100 行日誌。 |
| remove CONFIG.json | 刪除已停止的受管理容器及其系統紀錄；執行中請先 stop。 |
| multiple-deploy CONFIG.json COUNT | 建立或啟動 COUNT 個同專案實例，驗證每個網址並輸出各自的本機網址。 |
| multiple-remove CONFIG.json | 停止並刪除紀錄中名稱符合「專案名稱_site_流水號」的全部受管理實例，同時移除其紀錄。 |

單實例部署範例：

~~~cmd
python -m deploy_system.cli deploy project_config\site.json
echo %ERRORLEVEL%
python -m deploy_system.cli logs project_config\site.json
python -m deploy_system.cli stop project_config\site.json
python -m deploy_system.cli remove project_config\site.json
~~~

多實例部署範例：

~~~cmd
python -m deploy_system.cli multiple-deploy project_config\site.json 2
echo %ERRORLEVEL%
python -m deploy_system.cli multiple-remove project_config\site.json
echo %ERRORLEVEL%
~~~

多實例容器依序命名為「name_site_0」、「name_site_1」等，並綁定到 127.0.0.1 上由 Docker 分配的不同主機 Port。CLI 會列出各自的網址。COUNT 必須大於 0；如果紀錄中已有同名實例，系統會嘗試使用既有容器。multiple-remove 依名稱前綴處理整組受管理實例，不會只刪除前 COUNT 個。單實例指令仍以設定檔中的 name 為目標，不會自動改為操作整組多實例。

CLI 成功時結束碼為 0，失敗時為非零。HTTP 驗證以回應狀態碼 200 作為成功條件，單次請求逾時為 10 秒。Flask 映像檔建置逾時上限為 10 分鐘。部署或刪除中途失敗時，可檢查已建立的容器與系統紀錄。
