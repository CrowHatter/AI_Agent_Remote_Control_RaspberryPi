import os
import json
import time
import paramiko
from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from flask_cors import CORS
from openai import OpenAI
import pymongo

app = Flask(__name__)
swagger = Swagger(app)
CORS(app)

# === 1. 讀取 config.json 以取得敏感資訊 (例如 API Key) ===
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)
print("[INFO] 讀取 config.json 成功")

# === 2. 建立 OpenAI 之 Client 物件 ===
client_openai = OpenAI(api_key=config.get("OPENAI_API_KEY", ""))
print("[INFO] OpenAI Client 建立成功")

# === 3. 連線到 MongoDB ===
mongo_uri = "mongodb://localhost:27017"  # 請根據環境調整
mongo_client = pymongo.MongoClient(mongo_uri)
db = mongo_client["myflaskdb"]
chats_collection = db["chats"]
print("[INFO] 連線到 MongoDB 成功")

# === 幫助函式: 依 chat_id 取得聊天文件，若無則初始化 ===
def init_chat_if_not_exists(chat_id):
    chat_doc = chats_collection.find_one({"chat_id": chat_id})
    if not chat_doc:
        system_prompt = {
            "role": "system",
            "content": (
                "你是 Assistant1，負責與使用者互動並回應使用者對於 Raspberry Pi 的需求；"
                "但實際執行操作的工作由 Assistant2 代理完成。\n\n"
                "規範如下：\n"
                "1. 僅能以 Markdown 的形式回應，請務必使用適當的標題、段落與範例程式碼區塊。"
                "2. 在給定指令時，請將需要執行的指令以「```bash ...```」格式包覆。"
                "3. 第一行必須包含 cd 或其他完整路徑切換操作，並提供任何必要的 sudo 或安裝套件等指令；"
                "   切勿要求使用者手動切換目錄或安裝套件。"
                "4. 為了方便 Assistant2 自動執行，每個 Code Block 都必須是可以獨立執行的命令組合，"
                "   並在同一區塊中加上操作步驟或說明。"
                "5. 若指令需要多個步驟，請依照邏輯拆分成多個 Code Block，並在文字敘述中清楚解釋各步驟的意義與注意事項。"
                "6. 若經確認使用者的需求無法僅透過 Raspberry Pi CLI (命令列) 完成，請禮貌拒絕並說明理由。\n\n"
                "總結："
                "請像在編寫教學文件 (README.md) 一樣，仔細撰寫可在 Raspberry Pi 上直接執行的程式碼區塊與文字解說；"
                "Assistant2 會自動解析並執行你產生的 Code Block，因此務必確保其正確性與完整性。"
            )
        }
        new_chat_doc = {
            "chat_id": chat_id,
            "messages": [system_prompt]
        }
        chats_collection.insert_one(new_chat_doc)
        print(f"[INFO] 初始化聊天室 {chat_id} 完成")
        return new_chat_doc
    else:
        print(f"[INFO] 聊天室 {chat_id} 已存在")
        return chat_doc

# === Assistant1 聊天 API ===
@app.route('/assistant1/chat', methods=['POST'])
@swag_from({
    'tags': ['Assistant1'],
    'summary': 'Assistant1聊天 (POST)',
    'description': '使用 MongoDB 儲存對話紀錄，以 chat_id 作為索引',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'chat_id': {'type': 'string', 'description': '用於區分多個聊天室的ID'},
                    'user_message': {'type': 'string', 'description': '使用者對Raspberry Pi的自然語言需求'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': '成功回傳Assistant1的Markdown訊息',
            'schema': {
                'type': 'object',
                'properties': {
                    'assistant_markdown': {'type': 'string', 'description': 'Assistant1 的回覆Markdown'},
                    'chat_id': {'type': 'string', 'description': '聊天室ID'}
                }
            }
        }
    }
})
def assistant1_chat():
    data = request.json
    chat_id = data.get('chat_id', 'default')
    user_message = data.get('user_message', '')
    print(f"[INFO] Assistant1 聊天，chat_id: {chat_id}")
    
    chat_doc = init_chat_if_not_exists(chat_id)
    user_msg = {"role": "user", "content": user_message}
    chat_doc["messages"].append(user_msg)
    
    try:
        response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=chat_doc["messages"],
            temperature=0.7
        )
        assistant_reply = response.choices[0].message.content
        print("[INFO] Assistant1 回覆取得成功")
        assistant_msg = {"role": "assistant", "content": assistant_reply}
        chat_doc["messages"].append(assistant_msg)
        
        chats_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"messages": chat_doc["messages"]}}
        )
        
        return jsonify({
            "assistant_markdown": assistant_reply,
            "chat_id": chat_id
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Assistant1 呼叫失敗: {e}")
        return jsonify({"error": str(e)}), 500

# === 查詢聊天室歷史 API ===
@app.route('/assistant1/history/<string:chat_id>', methods=['GET'])
@swag_from({
    'tags': ['Assistant1'],
    'summary': '查詢聊天室歷史 (GET, MongoDB)',
    'description': '從 MongoDB chats_collection 中取出 messages',
    'parameters': [
        {
            'name': 'chat_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '聊天室 ID'
        }
    ],
    'responses': {
        200: {
            'description': '回傳該聊天室的所有訊息陣列',
            'schema': {
                'type': 'object',
                'properties': {
                    'chat_id': {'type': 'string'},
                    'history': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'role': {'type': 'string'},
                                'content': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_chat_history(chat_id):
    chat_doc = chats_collection.find_one({"chat_id": chat_id})
    if not chat_doc:
        chat_doc = init_chat_if_not_exists(chat_id)
    print(f"[INFO] 查詢聊天室 {chat_id} 歷史成功")
    return jsonify({
        "chat_id": chat_id,
        "history": chat_doc["messages"]
    }), 200

# === Assistant2 執行 API ===
@app.route('/assistant2/execute', methods=['POST'])
@swag_from({
    'tags': ['Assistant2'],
    'summary': 'Assistant2 執行指令 (POST)',
    'description': (
        "接收 markdown_content、chat_id 與 device_id，根據 Assistant1 產生的 Markdown 指令，"
        "透過 Assistant2 與 Raspberry Pi 進行多輪互動，最終將結果（Error 或 Complete）以 role:user 寫入 MongoDB 聊天記錄，"
        "並返回最終結果給前端，以便 Assistant1 產生新 Markdown。"
    ),
    'parameters': [
        {
            'name': 'chat_id',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': '聊天室 ID'
        },
        {
            'name': 'device_id',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'config.json 中定義的裝置 key'
        },
        {
            'name': 'markdown_content',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Assistant1 產生的 Markdown 指令'
        }
    ],
    'responses': {
        '200': {
            'description': 'Assistant2 執行完成，返回最終結果與更新後的聊天室記錄',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'final_result': {'type': 'string'},
                    'chat_id': {'type': 'string'},
                    'new_markdown': {'type': 'string'},
                    'messages': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'role': {'type': 'string'},
                                'content': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    }
})
def assistant2_execute():
    # 讀取表單參數（formData）
    chat_id = request.form.get("chat_id", "chat1")
    device_id = request.form.get("device_id", "Device1")
    markdown_content = request.form.get("markdown_content", "")
    print(f"[INFO] Assistant2 執行 API 呼叫，chat_id: {chat_id}, device_id: {device_id}")
    
    # 取得或初始化該聊天室記錄
    chat_doc = init_chat_if_not_exists(chat_id)
    
    # 建立 Assistant2 對話初始訊息 (系統提示自行補全，此處以 "省略" 表示)
    assistant2_system = (
        "你是 Assistant2，你要解析markdown資訊並逐步回傳行動指令，指令將透過 Paramiko 於遠端連線並操作 Raspberry Pi 的 CLI。"
        "你必須嚴格依照以下規範回覆，所有回覆均須以 JSON 格式輸出，且不得包含任何額外的 Markdown 或解說性文字。"
        "此外，回覆的第一行務必包含 ls檢視當前位置，再接著進行其他完整路徑切換行為(若當下步驟需要)，完成路竟切換後也須ls檢視是先前ls之資訊不同以確保路徑切換成功，否則系統無法自動完成路徑切換。輸出指令時不可使用code block(```)，必須直接輸出純文字。\n\n"
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
        "請務必依照以上規範回覆，所有回覆都必須僅以 JSON 格式輸出，且內容必須符合指定格式，不得包含任何額外文字。\n"
        "切記若是有使用ExecuteInvokeShellCommand，一般都會需要輸出ctrl+某案鍵以保存並退出shell。\n\n"
        "範例對話，假設markdown資訊為在桌面建立一hello.py會print Hello, World!:\n"
        "Assistant 回覆: {\"ExecuteCommand\": \"ls\"}\n"
        "User 回覆: CLI Output:\nBookshelf\nDesktop\nDocuments\nDownloads\nhello.py\nMusic\nPictures\nPublic\nTemplates\nVideos\n"
        "Assistant 回覆: {\"ExecuteCommand\": \"cd Desktop\"}\n"
        "User 回覆: CLI Output:\n"
        "Assistant 回覆: {\"ExecuteCommand\": \"echo 'print(\\\"Hello, World!\\\")' > hello.py\"}\n"
        "User 回覆: CLI Output:\n"
        "Assistant 回覆: {\"Complete\": \"All commands executed successfully.\"}"
    )
    messages = [
        {"role": "system", "content": assistant2_system},
        {"role": "user", "content": markdown_content}
    ]
    print("[INFO] Assistant2 對話初始訊息建立完成")
    
    # 讀取 device 連線資訊
    device_info = config["Device"].get(device_id)
    if not device_info:
        return jsonify({"error": f"Device {device_id} not found in config.json"}), 400
    hostname = device_info.get("hostname")
    username = device_info.get("username")
    password = device_info.get("password")
    print(f"[INFO] 讀取 Device {device_id} 連線資訊成功")
    
    # 建立 SSH 連線
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"[INFO] 嘗試連線到 {hostname} ...")
    try:
        ssh_client.connect(hostname=hostname, username=username, password=password, port=22)
    except Exception as e:
        return jsonify({"error": f"無法連線至 Raspberry Pi: {str(e)}"}), 500
    print("[INFO] SSH 連線建立成功")
    
    max_iterations = 15
    iteration_count = 0
    final_status = "Incomplete"
    final_result = ""
    
    while iteration_count < max_iterations:
        iteration_count += 1
        print(f"[INFO] Assistant2 互動回合 {iteration_count} 開始")
        try:
            response = client_openai.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7
            )
        except Exception as e:
            ssh_client.close()
            return jsonify({"error": f"OpenAI 呼叫失敗: {str(e)}"}), 500
        
        assistant_reply = response.choices[0].message.content
        print(f"\n=== Assistant2 Reply (Iteration {iteration_count}) ===")
        print(assistant_reply)
        messages.append({"role": "assistant", "content": assistant_reply})
        
        trimmed_reply = assistant_reply.strip()
        parsed = None
        if trimmed_reply.startswith("{"):
            try:
                parsed = json.loads(trimmed_reply)
            except Exception:
                print("[ERROR] JSON 解析失敗")
                parsed = None
        
        if parsed:
            if "Error" in parsed:
                final_status = "Error"
                final_result = parsed["Error"]
                print("[INFO] Assistant2 回傳 Error，結束互動")
                break
            elif "Complete" in parsed:
                final_status = "Complete"
                final_result = parsed["Complete"]
                print("[INFO] Assistant2 回傳 Complete，結束互動")
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
                    ssh_client.close()
                    return jsonify({"error": f"執行 CLI 指令失敗: {str(e)}"}), 500
                print(f"[CMD OUTPUT]\n{combined_output}")
                # 不記錄中間對話，只保留最終結果
            elif "ExecuteInvokeShellCommand" in parsed:
                command = parsed["ExecuteInvokeShellCommand"]
                print(f"[INFO] 執行互動式指令 (invoke_shell): {command}")
                try:
                    channel = ssh_client.invoke_shell()
                    channel.send(command + "\n")
                    time.sleep(2)
                    output = ""
                    while channel.recv_ready():
                        output += channel.recv(1024).decode('utf-8', errors='ignore')
                        time.sleep(0.5)
                    channel.close()
                except Exception as e:
                    ssh_client.close()
                    return jsonify({"error": f"執行互動式 CLI 指令失敗: {str(e)}"}), 500
                print(f"[CMD OUTPUT]\n{output}")
                # 不記錄中間對話
        else:
            ssh_client.close()
            return jsonify({"error": "Assistant2 回覆非 JSON 格式"}), 500
        
        print(f"[INFO] 回合 {iteration_count} 結束")
    
    ssh_client.close()
    
    # 僅將最終結果記錄到聊天室中
    final_message = {"role": "user", "content": json.dumps({final_status: final_result}, ensure_ascii=False)}
    chat_doc["messages"].append(final_message)
    chats_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"messages": chat_doc["messages"]}}
    )
    print("[INFO] 聊天記錄更新完成，僅記錄最終結果")
    
    # 將更新後的聊天室記錄餵給 Assistant1 以產生新的 Markdown 回覆
    try:
        new_response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=chat_doc["messages"],
            temperature=0.7
        )
    except Exception as e:
        return jsonify({"error": f"Assistant1 呼叫失敗: {str(e)}"}), 500
    new_markdown = new_response.choices[0].message.content
    print("[INFO] Assistant1 產生新 Markdown 回覆成功")
    chat_doc["messages"].append({"role": "assistant", "content": new_markdown})
    chats_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"messages": chat_doc["messages"]}}
    )
    
    return jsonify({
        "status": final_status,
        "final_result": final_result,
        "new_markdown": new_markdown,
        "chat_id": chat_id,
        "messages": chat_doc["messages"]
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
