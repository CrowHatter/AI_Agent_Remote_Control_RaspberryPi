from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from flask_cors import CORS  # <-- 新增：用於解決跨域
from openai import OpenAI
import pymongo
import os
import json

app = Flask(__name__)
# 啟用 Swagger
swagger = Swagger(app)

# 啟用 CORS，若只允許特定路徑或網域，也可加參數
# 例如：CORS(app, resources={r"/assistant1/*": {"origins": "http://localhost:8080"}})
CORS(app)

# === 1. 讀取 config.json 以取得敏感資訊 (例如 API Key) ===
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# === 2. 建立 OpenAI 之 Client 物件 ===
client_openai = OpenAI(api_key=config.get("OPENAI_API_KEY", ""))

# === 3. 連線到 MongoDB ===
mongo_uri = "mongodb://localhost:27017"  # 若你是 Docker 或雲端，換成相應連線URI
mongo_client = pymongo.MongoClient(mongo_uri)
db = mongo_client["myflaskdb"]  # 資料庫名稱
chats_collection = db["chats"]  # 專門存聊天紀錄的 collection

"""
chats_collection 結構範例:
{
  "_id": ObjectId(...),
  "chat_id": "1",
  "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."},
      ...
  ]
}
"""

# === 4. 幫助函式: 依 chat_id 取得聊天文件，若無則初始化 ===
def init_chat_if_not_exists(chat_id):
    chat_doc = chats_collection.find_one({"chat_id": chat_id})
    if not chat_doc:
        # 若無，則新建
        system_prompt = {
            "role": "system",
            "content": (
                "你是 Assistant1，負責回應 user 對於 Raspberry Pi 的操作需求，"
                "並在需要時協助解決 Raspberry Pi CLI 的錯誤。"
                "必須以 Markdown 格式回覆，並附上可直接執行的若干個 Code Block(例如 ```bash ...``` )。"
                "當作在撰寫一個API Document的README.md，針對每一個Code Block進行詳細的說明。"
                "第一行務必包含 cd 或其他完整路徑操作，切勿要求user自行操作路徑切換。"
                "若經確認user之需求無法透過於 Raspberry Pi 之CLI完成，請禮貌拒絕並說明理由。"
            )
        }
        new_chat_doc = {
            "chat_id": chat_id,
            "messages": [system_prompt]
        }
        chats_collection.insert_one(new_chat_doc)
        return new_chat_doc
    else:
        return chat_doc

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
                    'chat_id': {
                        'type': 'string',
                        'description': '用於區分多個聊天室的ID'
                    },
                    'user_message': {
                        'type': 'string',
                        'description': '使用者對Raspberry Pi的自然語言需求'
                    }
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
                    'assistant_markdown': {
                        'type': 'string',
                        'description': 'Assistant1 的回覆Markdown'
                    },
                    'chat_id': {
                        'type': 'string',
                        'description': '聊天室ID'
                    }
                }
            }
        }
    }
})
def assistant1_chat():
    data = request.json
    chat_id = data.get('chat_id', 'default')
    user_message = data.get('user_message', '')

    # 1) 取出或初始化該聊天室文件
    chat_doc = init_chat_if_not_exists(chat_id)

    # 2) 加入使用者訊息
    user_msg = {"role": "user", "content": user_message}
    chat_doc["messages"].append(user_msg)

    # 3) 呼叫 OpenAI chat.completions
    try:
        response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=chat_doc["messages"],
            temperature=0.7
        )
        assistant_reply = response.choices[0].message.content

        # 4) 將 assistant 回應加入 chat_doc
        assistant_msg = {"role": "assistant", "content": assistant_reply}
        chat_doc["messages"].append(assistant_msg)

        # 5) 更新 MongoDB
        chats_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"messages": chat_doc["messages"]}}
        )

        return jsonify({
            "assistant_markdown": assistant_reply,
            "chat_id": chat_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        # 如果還未建立，順便初始化
        chat_doc = init_chat_if_not_exists(chat_id)
    return jsonify({
        "chat_id": chat_id,
        "history": chat_doc["messages"]
    }), 200

if __name__ == '__main__':
    # debug=True 時，程式碼修改後可自動重啟；port=5000 可依需求變更
    app.run(debug=True, port=5000)
