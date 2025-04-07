import os
import json
import time
import paramiko
from openai import OpenAI

# 測試用的 Markdown 內容，請自行填入 Assistant1 的 Markdown 結果
USER_MARKDOWN = """
### 在桌面建立 Python 檔案\n\n首先，我們需要在桌面建立一個 Python 檔案，並在檔案中寫入程式碼來印出 "Hello, World!"。\n\n1. 首先，切換至桌面目錄：\n```bash\ncd ~/Desktop\n```\n\n2. 接著，使用以下指令建立一個新的 Python 檔案（例如 `hello.py`）：\n```bash\necho "print('Hello, World!')" > hello.py\n```\n\n### 編輯 Python 檔案\n\n現在我們已經在桌面建立了一個 Python 檔案 `hello.py`，接下來我們可以編輯這個檔案，讓它真正印出 "Hello, World!"。\n\n1. 使用以下指令編輯 `hello.py` 檔案：\n```bash\nnano hello.py\n```\n\n2. 在 Nano 編輯器中，將游標移至 `print('Hello, World!')` 這一行，修改程式碼或做任何其他必要的編輯。\n\n3. 按下 `Ctrl + X`，再依序按下 `Y` 確認儲存，最後按下 `Enter` 離開 Nano 編輯器。\n\n### 執行 Python 檔案\n\n最後，我們可以執行剛剛建立的 Python 檔案 `hello.py`，來印出 "Hello, World!"。\n\n1. 使用以下指令執行 `hello.py` 檔案：\n```bash\npython3 hello.py\n```\n\n透過以上步驟，您已在桌面建立了一個能印出 "Hello, World!" 的 Python 檔案並成功執行。如果有任何問題或需要進一步協助，請隨時讓我知道！
"""

# 設定要使用的 Device key (對應 config.json 中 Device 的 key)
DEVICE_ID = "Device1"

# 讀取 config.json
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 建立 OpenAI 之 Client 物件
client_openai = OpenAI(api_key=config.get("OPENAI_API_KEY", ""))

# 取得裝置連線資訊
device_info = config["Device"].get(DEVICE_ID)
if not device_info:
    raise ValueError(f"Device '{DEVICE_ID}' not found in config.json!")
HOSTNAME = device_info.get("hostname")
USERNAME = device_info.get("username")
PASSWORD = device_info.get("password")

# Assistant2 系統任務，內容以「省略」標記
assistant2_system = (
    "你是 Assistant2，你要解析markdown資訊並逐步回傳行動指令，指令將透過 Paramiko 於遠端連線並操作 Raspberry Pi 的 CLI。"
    "你必須嚴格依照以下規範回覆，所有回覆均須以 JSON 格式輸出，且不得包含任何額外的 Markdown 或解說性文字。"
    "此外，回覆的第一行務必包含 ls檢視當前位置，再接著進行其他完整路徑切換行為 (若當下步驟需要)，否則系統無法自動完成路徑切換。輸出指令時不可使用code block(```)，必須直接輸出純文字。\n\n"
    "1. 當你要執行純 CLI 指令時，請回覆如下 JSON 格式：\n"
    "{\"ExecuteCommand\": \"<打算執行之CLI指令>\"}\n\n"
    "2. 當你要執行需要 invoke_shell() 的互動式命令（例如 nano、crontab 等）時，請回覆如下 JSON 格式：\n"
    "{\"ExecuteInvokeShellCommand\": \"<打算執行之指令>\"}\n\n"
    "3. 當你判斷命令執行發生錯誤時，請立刻回覆以下 JSON 格式（之後不再輸出任何 CLI 指令）：\n"
    "{\"Error\": {\"ExecutedCommand\": \"<剛才執行的指令>\", \"RaspberryPiOutput\": \"<實際輸出結果>\", \"ExpectedBehavior\": \"<本應該看到或期望出現的結果描述>\"}}\n\n"
    "4. 當所有任務順利完成時，請回覆以下 JSON 格式（之後不再輸出任何 CLI 指令）：\n"
    "{\"Complete\": \"All commands executed successfully.\"}\n\n"
    "5. 每次你僅能回覆一條指令。回覆的第一行必須包含檢查當前位置（例如 ls），並在需要時進行目錄切換或其他必要操作，以保證後續指令能夠正確執行。\n\n"
    "6. 若 Markdown 中包含多個 Code Block，你應依序拆分並逐步執行，每次回覆僅提供一條指令，且不得混合多個指令。\n\n"
    "7. Paramiko 功能說明：\n"
    "   - 使用 exec_command() 執行非互動式命令；\n"
    "   - 使用 invoke_shell() 執行需要互動的命令（例如 nano、crontab）；\n"
    "   - 你必須根據執行結果判斷是否需要回覆 Error 或 Complete 格式的訊息。\n\n"
    "請務必依照以上規範回覆，所有回覆都必須僅以 JSON 格式輸出，且內容必須符合指定格式，不得包含任何額外文字。\n\n"
    "範例對話，假設markdown資訊為在桌面建立一hello.py會print Hello, World!:\n"
    "Assistant 回覆: {\"ExecuteCommand\": \"ls\"}\n"
    "User 回覆: CLI Output:\nBookshelf\nDesktop\nDocuments\nDownloads\nhello.py\nMusic\nPictures\nPublic\nTemplates\nVideos\n"
    "Assistant 回覆: {\"ExecuteCommand\": \"cd Desktop\"}\n"
    "User 回覆: CLI Output:\n"
    "Assistant 回覆: {\"ExecuteCommand\": \"echo 'print(\"Hello, World!\")' > hello.py\"}\n"
    "User 回覆: CLI Output:\n"
    "Assistant 回覆: {\"Complete\": \"All commands executed successfully.\"}"
)

# 初始對話訊息列表：第一則為系統訊息，第二則為 user 輸入 (Assistant1 產生的 Markdown)
messages = [
    {"role": "system", "content": assistant2_system},
    {"role": "user", "content": USER_MARKDOWN}
]

# 建立 Paramiko SSH 連線到 Raspberry Pi
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print(f"[INFO] 嘗試連線到 {HOSTNAME} ...")
try:
    ssh_client.connect(hostname=HOSTNAME, username=USERNAME, password=PASSWORD, port=22)
except Exception as e:
    print(f"[ERROR] 無法連線至 Raspberry Pi: {e}")
    exit(1)
print("[INFO] 成功連線到 Raspberry Pi!")

max_iterations = 10
iteration_count = 0
final_status = "Incomplete"
final_result = ""

while iteration_count < max_iterations:
    iteration_count += 1
    try:
        response = client_openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
    except Exception as e:
        print(f"[ERROR] OpenAI 呼叫失敗: {e}")
        break

    assistant_reply = response.choices[0].message.content
    print(f"\n=== Assistant2 Reply (Iteration {iteration_count}) ===")
    print(assistant_reply)
    # 將 Assistant2 回覆加入對話，角色為 assistant
    messages.append({"role": "assistant", "content": assistant_reply})

    # 嘗試解析 JSON 格式回覆
    trimmed_reply = assistant_reply.strip()
    parsed = None
    if trimmed_reply.startswith("{"):
        try:
            parsed = json.loads(trimmed_reply)
        except Exception:
            pass

    if parsed:
        if "Error" in parsed:
            final_status = "Error"
            final_result = parsed["Error"]
            messages.append({"role": "user", "content": json.dumps({"Error": final_result}, ensure_ascii=False)})
            break
        elif "Complete" in parsed:
            final_status = "Complete"
            final_result = parsed["Complete"]
            messages.append({"role": "user", "content": json.dumps({"Complete": final_result}, ensure_ascii=False)})
            break
        elif "ExecuteCommand" in parsed:
            command = parsed["ExecuteCommand"]
            print(f"[INFO] 執行非互動式 CLI 指令: {command}")
            try:
                stdin, stdout, stderr = ssh_client.exec_command(command)
                cmd_output = stdout.read().decode('utf-8', errors='ignore')
                cmd_err = stderr.read().decode('utf-8', errors='ignore')
                combined_output = (cmd_output + "\n" + cmd_err).strip()
            except Exception as e:
                print(f"[ERROR] 執行 CLI 指令失敗: {e}")
                break
            print(f"[CMD OUTPUT]\n{combined_output}")
            messages.append({"role": "user", "content": f"CLI Output:\n{combined_output}"})
        elif "ExecuteInvokeShellCommand" in parsed:
            command = parsed["ExecuteInvokeShellCommand"]
            print(f"[INFO] 執行互動式指令 (invoke_shell): {command}")
            try:
                channel = ssh_client.invoke_shell()
                # 設定超時或等待足夠時間以獲取輸出
                channel.send(command + "\n")
                time.sleep(2)
                output = ""
                while channel.recv_ready():
                    output += channel.recv(1024).decode('utf-8', errors='ignore')
                    time.sleep(0.5)
                channel.close()
            except Exception as e:
                print(f"[ERROR] 執行互動式指令失敗: {e}")
                break
            print(f"[CMD OUTPUT]\n{output}")
            messages.append({"role": "user", "content": f"CLI Output:\n{output}"})
    else:
        # 如果無法解析 JSON，則視為錯誤
        print("[ERROR] Assistant2 回覆無法解析為 JSON 格式")
        break

ssh_client.close()

if final_status == "Incomplete":
    final_status = "Error"
    final_result = {
        "ExecuteCommand": "N/A",
        "RaspberryPiOutput": "",
        "ExpectedBehavior": "Assistant2 執行回合過多，可能陷入迴圈"
    }
    messages.append({"role": "user", "content": json.dumps({"Error": final_result}, ensure_ascii=False)})

print("\n=== 最終結果 ===")
print(f"Final Status: {final_status}")
print(f"Final Result: {final_result}")

# 將完整對話紀錄寫入 Testlog.json
log_path = os.path.join(os.path.dirname(__file__), "Testlog.json")
with open(log_path, "w", encoding="utf-8") as log_file:
    json.dump(messages, log_file, ensure_ascii=False, indent=2)
print(f"[INFO] 對話紀錄已寫入 {log_path}")
