from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from openai import OpenAI
import json
import os

app = Flask(__name__)
swagger = Swagger(app)

# === 1. 讀取 config.json 以取得敏感資訊 (例如 API Key) ===
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# === 2. 建立 OpenAI 之 Client 物件 ===
client = OpenAI(api_key=config.get("OPENAI_API_KEY", ""))

# === 3. 暫存對話記錄 (用於多聊天室) ===
chats_memory = {}

def init_chat_if_not_exists(chat_id):
    """若該 chat_id 尚未在記憶體中，則初始化一個空的對話陣列，
       並插入一段 system prompt 告知 Assistant1 他的任務。"""
    if chat_id not in chats_memory:
        # 先建立空陣列
        chats_memory[chat_id] = []
        # 在這裡插入 system prompt (role: "system")
        chats_memory[chat_id].append({
            "role": "system",
            "content": (
                "你是 Assistant1，負責回應user對於 Raspberry Pi 的操作需求，"
                "並在需要時協助解決 Raspberry Pi CLI 的錯誤。"
                "必須以 Markdown 格式回覆，並附上可直接執行的若干個 Code Block(例如 ```bash ...``` )。"
                "當作在撰寫一個API Document的README.md，針對每一個Code Block進行詳細的說明"
                "第一行務必包含 cd 或其他完整路徑操作，切勿要求user自行操作路徑切換。"
                "若經確認user之需求無法透過於 Raspberry Pi 之CLI完成，請禮貌拒絕並說明理由。"
            )
        })

# === 4. POST: Assistant1 Chat 接口 ===
@app.route('/assistant1/chat', methods=['POST'])
@swag_from({
    'tags': ['Assistant1'],
    'summary': 'Assistant1聊天 (POST)',
    'description': 'Assistant1 接收user對 Raspberry Pi 的操作需求並回傳 Markdown 包含可執行的 Code Block。',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'chat_id': {
                        'type': 'string',
                        'description': '用於區分多個聊天室的ID'
                    },
                    'user_message': {
                        'type': 'string',
                        'description': 'user對Raspberry Pi的自然語言操作需求'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': '成功回傳 Assistant1 的 Markdown 訊息',
            'schema': {
                'type': 'object',
                'properties': {
                    'assistant_markdown': {
                        'type': 'string',
                        'description': 'Assistant1 產生的 Markdown (內含可能有 Code Block)'
                    },
                    'chat_id': {
                        'type': 'string',
                        'description': '聊天室ID'
                    }
                }
            }
        },
        500: {
            'description': '伺服器錯誤或 OpenAI 請求錯誤'
        }
    }
})
def assistant1_chat():
    data = request.json
    chat_id = data.get('chat_id', 'default')
    user_message = data.get('user_message', '')

    # 若不存在此 chat_id，則初始化 (含 system prompt)
    init_chat_if_not_exists(chat_id)

    # 新增一則user訊息
    chats_memory[chat_id].append({
        "role": "user",
        "content": user_message
    })

    try:
        # 呼叫 ChatCompletions
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=chats_memory[chat_id],
            temperature=0.7
        )
        assistant_reply = response.choices[0].message.content

        # 將 Assistant 的回應存入對話記錄
        chats_memory[chat_id].append({
            "role": "assistant",
            "content": assistant_reply
        })

        return jsonify({
            "assistant_markdown": assistant_reply,
            "chat_id": chat_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === 5. GET: 取得聊天室的所有對話紀錄 ===
@app.route('/assistant1/history/<string:chat_id>', methods=['GET'])
@swag_from({
    'tags': ['Assistant1'],
    'summary': '查詢某個聊天室的對話紀錄 (GET)',
    'description': '回傳該 chat_id 內所有的訊息陣列，包括 role 與 content',
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
            'description': '成功回傳對應聊天室的所有訊息',
            'schema': {
                'type': 'object',
                'properties': {
                    'chat_id': {
                        'type': 'string'
                    },
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
    init_chat_if_not_exists(chat_id)
    return jsonify({
        "chat_id": chat_id,
        "history": chats_memory[chat_id]
    })

# === 主程式入口 ===
if __name__ == '__main__':
    app.run(debug=True, port=5000)
