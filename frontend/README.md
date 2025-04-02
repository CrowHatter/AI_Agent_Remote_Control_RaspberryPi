# My Chat App

這個專案使用 Vue 3 建構，包含前端與後端部分。以下步驟將協助你在新設備上重建開發環境。

> **注意：**  
> Markdown 文件中的 code block 區域請務必使用三個 backticks (```) 包裹，並在需要時指定語言（例如：`bash`、`js`、`vue` 等），以確保語法高亮及正確顯示。如果發現 code block 顯示異常，可參考此範例格式進行調整。

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

## Markdown Code Block 的處理說明

- 當你在 Markdown 文件內書寫 code block 時，請使用三個 backticks 包裹程式碼區塊。例如，下面這個範例示範如何在 README 中顯示啟動命令：

  ```bash
  npm run serve
  ```

- 如果需要指定語言（以便語法高亮），請在開頭的三個 backticks 後面加入語言名稱，例如：

  ```js
  console.log("Hello, world!");
  ```

- 若遇到 code block 顯示異常，請檢查是否有額外的空白或不正確的符號，並參照上述範例進行修正。

## 疑難排解

- **Node.js 或 npm 版本不符：**  
  請確認你已更新至最新版本。使用 `node -v` 與 `npm -v` 檢查版本。

- **依賴安裝失敗：**  
  若遇到 npm 依賴安裝問題，可以嘗試刪除 `node_modules` 資料夾並重新執行 `npm install`。

- **其他問題：**  
  請檢查瀏覽器 Console 及終端機訊息，若有疑問可參考官方文件或提出 issue.
