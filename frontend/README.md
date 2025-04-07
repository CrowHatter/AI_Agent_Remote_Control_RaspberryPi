# My Chat App

此專案為 Raspberry Pi AI Agent 的前端程式碼，採用 Vue3 框架開發。

## 前置需求

- **Node.js**  
  請確保你的 Node.js 版本為 14 以上（建議使用最新 LTS 版）。你可以從 [Node.js 官網](https://nodejs.org/) 下載或使用版本管理工具（例如 nvm）更新。

- **npm**  
  建議更新至最新版本。你可以透過下列命令更新 npm：
  
  ```bash
  npm install -g npm@latest
  ```

## 環境重建步驟

1. **進入專案資料夾**

   ```bash
   cd my-chat-app
   ```

2. **安裝 Vue CLI (如果尚未安裝)**

   此專案使用 Vue 3，如果你還沒安裝 Vue CLI，請執行下列命令：

   ```bash
   npm install -g @vue/cli
   ```

   安裝完成後，你可以透過下列命令檢查版本：

   ```bash
   vue --version
   ```

3. **安裝專案依賴**

   在專案資料夾中執行：

   ```bash
   npm install
   ```

   此命令會根據 `package.json` 自動下載並安裝所有必要的 npm 套件。

   - 如出現問題，你可能需要執行以下指令新增環境變數
      ```bash
      $Env:Path += ";C:\Program Files\nodejs"
      ```

4. **啟動開發伺服器**

   安裝完成後，執行以下命令啟動開發伺服器：

   ```bash
   npm run serve
   ```

   執行後，瀏覽器會自動開啟並載入專案（預設網址通常是 [http://localhost:8080](http://localhost:8080)）。
