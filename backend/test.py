from flask import Flask, jsonify, request
from flasgger import Swagger, swag_from

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/hello', methods=['GET'])
@swag_from({
    'tags': ['Hello API'],
    'description': '回傳問候字串',
    'responses': {
        200: {
            'description': '成功回傳結果',
            'examples': {
                'application/json': {
                    'message': 'Hello, Flask!'
                }
            }
        }
    }
})
def hello_world():
    return jsonify({'message': 'Hello, Flask!'})

if __name__ == '__main__':
    # 預設啟動後可以在 http://localhost:5000/apidocs 檢視 Swagger UI
    app.run(debug=True)
