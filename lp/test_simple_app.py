from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'アプリケーションは正常に動作しています'}

if __name__ == '__main__':
    print("🚀 シンプルアプリケーション起動中...")
    print("📡 ポート 5002 で起動します")
    app.run(debug=True, host='0.0.0.0', port=5002) 