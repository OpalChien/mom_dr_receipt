# mom_dr 收據紀錄 Streamlit App

這個專案會建立一個可部署到 Streamlit Community Cloud 的收據紀錄工具：

- 可切換中文 / English
- 可依照資料夾中的收據範例建立收據畫面
- 每次儲存會寫入 `mom_dr收據_log` Google 試算表
- 尚未設定 Google 時，會先寫入本機 `mom_dr_receipt_log.csv`

## 本機執行

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Google Sheets / Drive 設定

1. 到 Google Cloud 建立一個 Project。
2. 啟用 Google Sheets API 和 Google Drive API。
3. 建立 Service Account，下載 JSON key。
4. 把 JSON key 內容轉成 `.streamlit/secrets.toml` 格式，可參考 `.streamlit/secrets.toml.example`。
5. 如果希望試算表出現在你的 Google Drive 資料夾：
   - 在 Google Drive 建立或選擇一個資料夾。
   - 把該資料夾分享給 service account 的 `client_email`，權限設為編輯者。
   - 把資料夾網址裡的 folder id 填到 `google_drive_folder_id`。
6. 把 `share_with_email` 填成你的 Gmail，app 第一次建立 `mom_dr收據_log` 時會把試算表分享給你。

## 部署到 Streamlit Community Cloud

Streamlit 官方文件目前仍是從 [share.streamlit.io](https://share.streamlit.io/) 建立 app，部署後會得到 `streamlit.app` 網址。官方部署頁面說明需要在 Community Cloud 選擇 GitHub repo、branch、入口檔案，並可在 Secrets 欄位貼上 `secrets.toml` 內容。

1. 把這個資料夾推到 GitHub repo。
2. 到 [share.streamlit.io](https://share.streamlit.io/) 登入。
3. 點 Create app，選你的 repo、branch，Main file path 填 `app.py`。
4. 在 Advanced settings / Secrets 貼上 `.streamlit/secrets.toml` 的內容。
5. Deploy。

參考：Streamlit 官方文件 [Deploy your app on Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)。
