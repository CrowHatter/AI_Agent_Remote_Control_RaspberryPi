# AI_Agent_Remote_Control_RaspberryPi

本專案為 **Raspberry Pi AI Agent**，結合 **前端 Vue3 應用** 與 **後端 Flask API**，透過兩個 GPT-4o AI Agent 提供遠端控制 Raspberry Pi 的能力。整體架構如下：

- 前端介面供使用者輸入自然語言需求，並查看指令與執行結果。
- 後端分為兩個角色：  
  - `Assistant1`：解析使用者需求並產出防呆、可執行的 CLI 指令（以 Markdown 呈現）  
  - `Assistant2`：讀取 `Assistant1` 的指令，透過 SSH 遠端連線至 Raspberry Pi 並執行指令，回傳結果以供對話更新  

---

## 📦 前端 (Frontend) - Vue3

### 前置需求

- **Node.js**  
  請確保你的 Node.js 版本為 14 以上（建議使用最新 LTS 版）。你可以從 [Node.js 官網](https://nodejs.org/) 下載或使用版本管理工具（例如 nvm）更新。

- **npm**  
  建議更新至最新版本。你可以透過下列命令更新 npm：

  ```
  npm install -g npm@latest
  ```

### 環境重建步驟

1. **進入專案資料夾**

   ```
   cd FRONTEND/my-chat-app
   ```

2. **安裝 Vue CLI (如果尚未安裝)**

   ```
   npm install -g @vue/cli
   vue --version
   ```

3. **安裝專案依賴**

   ```
   npm install
   ```

   如出現問題，你可能需要執行以下指令新增環境變數：

   ```
   $Env:Path += ";C:\Program Files\nodejs"
   ```

4. **啟動開發伺服器**

   ```
   npm run serve
   ```

   預設網址：[http://localhost:8080](http://localhost:8080)

---

## 🖥️ 後端 (Backend) - Flask

此專案整合兩個 GPT-4o AI Agent：

- **Assistant1**  
  解析自然語言輸入，產生防呆、細節明確的 CLI 指令，並以 Markdown 格式呈現（包含 code block）

- **Assistant2**  
  解析 Assistant1 的 Markdown 指令（JSON 格式），透過 Paramiko 連接 Raspberry Pi 執行指令，並將結果回傳給 Assistant1 更新對話內容。

---

### 使用技術

- **程式語言**：Python  
- **框架**：Flask  
- **說明文件**：Flasgger  
- **CORS 處理**：Flask-CORS  
- **資料庫**：MongoDB  
- **SSH 操作**：Paramiko  
- **AI 模型**：OpenAI GPT-4o  
- **容器化**：Docker

---

### 環境建置步驟

1. **安裝 Docker**

   前往 [Docker 官方網站](https://www.docker.com/get-started) 安裝。

2. **安裝 MongoDB（使用 Docker）**

   ```
   docker run -d --name mongodb -p 27017:27017 -v mongodb_data:/data/db mongo
   ```

3. **建立 `config.json`**

   在 `BACKEND` 資料夾下建立：

   ```
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

   - **Windows：**

     ```
     python -m venv .venv
     .\.venv\Scripts\activate
     pip install -r requirements.txt
     ```

   - **macOS / Linux：**

     ```
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```

---

### 啟動 Flask 應用程式

請先確保 MongoDB 與 Docker 已啟動，然後執行：

```
python app.py
```

系統將於 [http://localhost:5000](http://localhost:5000) 提供 API 介面，並可透過：

- Swagger UI：[http://127.0.0.1:5000/apidocs](http://127.0.0.1:5000/apidocs)  
- Postman 或自製前端進行測試

---
[⬇️ 下載報告（PDF）](./slide.pdf)