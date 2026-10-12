自動部署系統使用說明
## 1. 專案目標

## 2. 使用情境與操作範例


### 情境 A：靜態網站

預期輸入: 使用者在指定資料夾中存放html檔案
操作:
    完整部署:
        系統會自動執行檢查與部署兩動作
    檢查:
        系統會有使專案可以運行的最低標準檢查
        系統可以讓使用者自行調整要新增哪些檢查
輸出: 網站成功部署後會顯示運行的狀態，連線IP，否則會顯示錯誤訊息

### 情境 B：Flask 網站

預期輸入: 使用者給一個 Flask 專案存放在指定位置，或者操作系統選擇該專案
操作:
    完整部署:
        系統會自動執行檢查與部署兩動作
    檢查:
        系統會有使專案可以運行的最低標準檢查
        系統可以讓使用者自行調整要新增哪些檢查
輸出: 網站成功部署後會顯示運行的狀態，連線IP，否則會顯示錯誤訊息

### 失敗案例情境:
    1.http回應測試未通過

    2.python語法未通過，導致無法啟動網站或者程式無法正確運行

    3.port衝突無法使用(已被占用)

    4.容器啟動錯誤

    5.設定檔錯誤

#定義通過檢查不但container 要 running 且 http 要回傳200，否則網站不算成功運行
#如果http有錯誤，但pytest正常還是應提示錯誤

## 3.使用規則


請檢查app.py有正確傳入config資料夾路徑

## 5. 異常狀況處理規則
    1. docker service:
        docker service中會先做紀錄檔比對，比對後會回傳結果
        回傳結果1: 找不到同名容器
        回傳結果2: 非本系統管理之容器不做操作
        回傳結果10:系統出現錯誤，同名同ID卻不同port/label/project_path



container_comparator太麻煩所以是直接用AI製作的

## Flask 專案的 Dockerfile 規格

Flask 專案使用者提供 app.py、requirements.txt 與 .dockerignore
預設容器使用 Python 3.12，建置時安裝 requirements.txt，啟動時執行 app.py。JSON 
設定檔的 port 是主機連接埠，container_port 是 Flask 在容器內監聽的連接埠（未填時預設為 8000
使用者的程式需在容器內監聽 0.0.0.0 與設定的 container_port。

系統會先檢查 app.py、requirements.txt 與 .dockerignore。
若只缺少Dockerfile，便自動建立使用 Python 3.12 的預設檔案；若使用者已提供Dockerfile，系統會保留並使用該檔案建置。

設定檔的內容若與 Python 程式的實際設定不一致（例如監聽位址或連接埠不同），目前不在系統自動修正範圍內，需由使用者自行調整。
