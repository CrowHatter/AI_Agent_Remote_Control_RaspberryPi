import openai
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

openai.api_key = config.get("OPENAI_API_KEY", "")

models = openai.models.list()

for model in models:
    print(model.id)
