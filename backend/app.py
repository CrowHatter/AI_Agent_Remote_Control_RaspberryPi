from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from openai import OpenAI  # 這裡是新版套件核心
import json
import os

app = Flask(__name__)
swagger = Swagger(app)

# === 1. 讀取 config.json 以取得敏感資訊 (例如 API Key) ===
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# === 2. 建立 OpenAI 之 Client 物件 ===
client = OpenAI(
    api_key=config.get("OPENAI_API_KEY", ""),
)

# === 3. 暫存對話記錄 ===
chats_memory = {}

def init_chat_if_not_exists(chat_id):
    """若該 chat_id 尚未在記憶體中，則初始化一個空的對話陣列。"""
    if chat_id not in chats_memory:
        chats_memory[chat_id] = []

@app.route('/assistant1/chat', methods=['POST'])
@swag_from({
    'tags': ['Assistant1'],
    'description': 'Assistant1 接收使用者對 Raspberry Pi 的自然語言需求並回傳 Markdown',
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
                        'description': '用於區分多個聊天室的ID（可自行定義，如: "1", "2"...）'
                    },
                    'user_message': {
                        'type': 'string',
                        'description': '使用者對Raspberry Pi的操作需求(自然語言)'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': '成功回傳Assistant1之Markdown訊息',
            'schema': {
                'type': 'object',
                'properties': {
                    'assistant_markdown': {
                        'type': 'string',
                        'description': 'Assistant1產生的Markdown內容'
                    },
                    'chat_id': {
                        'type': 'string',
                        'description': '回傳原樣的 chat_id'
                    }
                }
            }
        }
    }
})
def assistant1_chat():
    """
    Assistant1 提供自然語言聊天，並回傳包含CodeBlock的Markdown
    """
    data = request.json
    chat_id = data.get('chat_id', 'default')
    user_message = data.get('user_message', '')

    # 1) 若不存在此 chat_id，則初始化
    init_chat_if_not_exists(chat_id)

    # 2) 加入使用者訊息到對話
    chats_memory[chat_id].append({
        "role": "user",
        "content": user_message
    })

    try:
        # === 3) 新版: 使用 client.chat.completions.create(...) ===
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 暫用 GPT-3.5
            messages=chats_memory[chat_id],
            temperature=0.7
        )
        assistant_reply = response.choices[0].message.content

        # 以Markdown為回傳格式
        assistant_markdown = assistant_reply

        # 4) 將 Assistant 的回應存入對話記錄
        chats_memory[chat_id].append({
            "role": "assistant",
            "content": assistant_markdown
        })

        return jsonify({
            "assistant_markdown": assistant_markdown,
            "chat_id": chat_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/assistant1/history/<string:chat_id>', methods=['GET'])
@swag_from({
    'tags': ['Assistant1'],
    'description': '取得對應 chat_id 的全部對話紀錄',
    'parameters': [
        {
            'name': 'chat_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '聊天室ID'
        }
    ],
    'responses': {
        200: {
            'description': '回傳該聊天室所有訊息',
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
    init_chat_if_not_exists(chat_id)
    return jsonify({
        "chat_id": chat_id,
        "history": chats_memory[chat_id]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
