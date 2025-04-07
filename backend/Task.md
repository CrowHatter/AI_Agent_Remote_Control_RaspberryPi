# Flask 後端建置待辦事項清單

以下為本專案在 Flask 後端所需的建置與流程規劃，包含 `config.json`、兩個 OpenAI Assistants、任務佇列 (Task Queue) 與執行流程等，請依照此待辦清單進行開發。

## 1. 建立 `config.json`
- **目的**：儲存 API Key 等敏感資訊，以避免將金鑰或隱私資訊暴露在程式碼中。
- **建議做法**：
  1. 在專案根目錄新增一個 `config.json` 檔案。
  2. 檔案內容可用 JSON 格式紀錄，範例：
     ```json
     {
       "OPENAI_API_KEY": "your_openai_api_key_here",
       "DeviceIP": {
        "Device1": "192.168.1.104"
      }
     }
     ```
  3. 請確保將 `config.json` 加入 `.gitignore`，避免上傳至版本控制系統或公開儲存庫。

## 2. 建立兩個 Assistant：Assistant1 與 Assistant2
- **Assistant1**：
  1. 接收使用者傳來的「自然語言操作需求」(針對 Raspberry Pi 的操作)。
  2. 回覆時需以 **Markdown** 格式進行，且在回覆中包含「防呆且細節明確的 Code Block」。
     - 例如在 Code Block 的指令中，第一行就先執行 `cd`，不要僅告知使用者前往哪個目錄。
  3. 每次的對話都需要保存至資料庫或檔案系統的「聊天室(1~n)」，以便後續可以持續關聯同一上下文。

- **Assistant2**：
  1. 負責**實際在 Raspberry Pi 上執行**由 Assistant1 產生的指令。
  2. 針對每一個要執行的任務 (CLI 指令) 只回傳「應執行的 CLI 指令字串」，不回傳任何額外的自然語言內容。
  3. 在執行完 CLI 指令並取得執行結果後，會再次接收該執行結果並判斷是否正確：
     - 若正確，完成此任務 (Task) 後清空暫時聊天並執行下一 Task。
     - 若錯誤，則將錯誤結果與當前 Task/Task Queue 資訊回傳給 Assistant1，並清空當前 Task 與暫時聊天，讓 Assistant1 重新生成修改後的 Code Block。

## 3. 整體工作流程
1. **使用者輸入自然語言需求** → 傳給 **Assistant1**。
2. **Assistant1 以 Markdown 回覆** (內含 Code Block) → 儲存對話記錄至聊天室(1~n)。
3. **使用者有兩個選擇**：
   - (A) 繼續輸入自然語言需求 → 再次傳給 Assistant1 → 產生新 Markdown 回覆 (並更新聊天室記錄)。
   - (B) **Click "Accept and execute" 按鈕** → 從 Assistant1 的**最新一則回覆**中，提取每個 Code Block → 每個 Code Block 皆建立一個 **Task** → 加入 **Task Queue**。
4. **Assistant2** 開始處理 **Task Queue**：
   1. 取得當前 Task (CLI 指令) → Assistant2 僅回覆「應該執行的 CLI 命令」(視作在根目錄下執行)。
   2. 將該命令真實執行於 Raspberry Pi → 擷取執行結果訊息 → 回傳給 Assistant2。
   3. Assistant2 判斷結果：
      - 若 **正確** → 此 Task 完成 → 清空與此 Task 的暫時聊天 → 進入下一個 Task。
      - 若 **錯誤** → 回傳錯誤訊息、當前 Task、Task Queue 給 Assistant1 → 清空當前 Task 與暫時聊天 → 等待 Assistant1 輸出新的 Markdown。
5. **完成所有 Task** → 回傳給 Assistant1 `Task complete` → Assistant1 產生「不含 Code Block」的 Markdown 提示所有任務已完成。

## 4. Task 資料結構範例 (待實作)
以下是一個建議結構，可視需求微調：
```json
[
  {
    "taskId": 1,
    "cliCommand": "cd /home/pi && sudo apt-get update",
    "status": "PENDING",  
    "result": null,
    "assistant1MarkdownSource": "此欄可儲存整份 Assistant1 的 Markdown 以備查"
  },
  {
    "taskId": 2,
    "cliCommand": "sudo apt-get install python3-pip",
    "status": "PENDING",
    "result": null,
    "assistant1MarkdownSource": "此欄可儲存整份 Assistant1 的 Markdown 以備查"
  }
]
```
- taskId：任務唯一識別。  
- cliCommand：實際執行的 CLI 指令。  
- status：任務狀態，如 PENDING、IN_PROGRESS、COMPLETED、ERROR。  
- result：執行完畢後的結果或錯誤資訊。  
- assistant1MarkdownSource：可選，儲存來自 Assistant1 的完整 Markdown，方便日後追蹤來源。

## 5. 開發步驟建議  
- **建立 Flask 專案**：初始化基本結構 (如 app.py)，並安裝必要套件 (如 pip install flask、pip install openai 等)。  
- **載入 config.json**：  
  - 在 app.py 或專門的設定檔中讀取 config.json。  
  - 儲存 API Key 等敏感資訊到變數，以供 Assistant1、Assistant2 調用。  
- **撰寫 Assistant1**：  
  - 提供 API 端點 (e.g. /assistant1)。  
  - 負責接收使用者自然語言，透過 OpenAI API (GPT) 產生 Markdown 回覆 (含 Code Block)。  
  - 將對話紀錄保存到資料庫或檔案 (聊天室概念)。  
- **撰寫 Assistant2**：  
  - 提供 API 端點 (e.g. /assistant2)。  
  - 收到 Task Queue 中的任務後，只回傳應執行的 CLI 命令 (無多餘自然語言)。  
  - 接收命令執行結果並判斷是否正確，然後通知外部系統任務的執行狀態。  
- **實作 Task Queue**：  
  - 使用資料結構(如上)或佇列(如 Redis、RabbitMQ 等)儲存待執行的任務。  
  - 完成/錯誤時及時更新狀態並繼續/中斷流程。  
- **整合與測試**：  
  - 在前端或 API 介面中提供「Accept and execute」按鈕：  
    - 按下後自動從最新 Assistant1 回覆中擷取 Code Block，產生 Task，送入 Task Queue。  
    - 監聽並顯示 Raspberry Pi 執行結果，若全部執行完畢則顯示 Task 完成的 Markdown (Assistant1 所生成)。  
    - 若錯誤則顯示錯誤訊息並提示使用者更新需求。

6. 注意事項  
- **安全性**：切記不要直接將使用者輸入的內容 (尤其 CLI 命令) 全盤信任並在 Raspberry Pi 上執行，需做好權限與安全機制。  
- **錯誤處理**：Assistant2 如果收到多次錯誤結果，應確保不會重覆執行可能導致系統不穩定的指令。  
- **程式碼維護**：建議將 Assistant1、Assistant2、Task Queue 等模組化，便於維護與調整。  

以上為 Flask 後端建置的待辦事項清單與流程說明，請參考此步驟完成專案。