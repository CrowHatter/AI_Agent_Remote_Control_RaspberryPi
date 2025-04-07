# Raspberry Pi AI Agent Backend

此專案為 Raspberry Pi AI Agent 的後端程式碼，採用 Flask 框架開發，整合了兩個 GPT-4o AI Agent：

- **Assistant1**  
  負責接收使用者以自然語言描述的需求，並回覆防呆且細節明確的 Markdown 格式訊息，訊息中包含可直接在 Raspberry Pi 執行的 CLI 指令（以 Code Block 呈現）。

- **Assistant2**  
  負責解析 Assistant1 所回傳的 Markdown 指令（以 JSON 格式回覆），並利用 Paramiko 連線至 Raspberry Pi，依序執行 CLI 指令。Assistant2 僅回覆應執行的指令字串，不包含額外的自然語言解說，並根據命令執行結果判斷是否正確、錯誤或完成，最終將結果回傳給 Assistant1 更新對話內容。

---

## 使用技術

- **程式語言**：Python  
- **後端框架**：Flask  
- **API 說明文件**：Flasgger  
- **跨來源資源共享**：Flask-CORS  
- **資料庫**：MongoDB  
- **SSH 遠端連線**：Paramiko  
- **OpenAI API**：用於呼叫 GPT-4o AI Agent  
- **容器化工具**：Docker

---

## 環境建置順序

1. **下載並安裝 Docker**  
   前往 [Docker 官方網站](https://www.docker.com/get-started) 下載並安裝 Docker。

2. **下載並安裝 MongoDB**  
   可參考 [MongoDB 官方下載頁面](https://www.mongodb.com/try/download/community) 或使用下列指令：

   ```bash
   docker run -d --name mongodb -p 27017:27017 -v mongodb_data:/data/db mongo
   ```
3. **建立 `config.json`**  
   在專案`BACKEND`目錄下建立 `config.json`，範例如下（請自行填入正確的 API 金鑰與裝置資訊）：

   ```json
   {
       "OPENAI_API_KEY": "your_openai_api_key_here",
       "Device": {
           "Device1": {
               "hostname": "your_RaspberryPi_ip",
               "username": "your_username",
               "password": "your_password"
           }
       }
   }
   ```

4. **建立虛擬環境與安裝套件**

   請依照你的作業系統執行下列指令：

   **Windows：**

   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
   **macOS / Linux：**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## 執行方式

   確保 MongoDB 與 Docker 已啟動。
   啟動 Flask 應用：

```bash
python app.py
```
系統將在 http://localhost:5000 提供 API 介面。

可透過 http://127.0.0.1:5000/apidocs Swagger UI、自製前端或 Postman 測試。

