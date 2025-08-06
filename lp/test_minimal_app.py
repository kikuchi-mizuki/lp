from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'アプリケーションは正常に動作しています'})

@app.route('/test')
def test():
    return jsonify({'test': 'success'})

if __name__ == '__main__':
    print("🚀 最小限アプリケーション起動中...")
    print("📡 ポート 5003 で起動します")
    app.run(debug=False, host='0.0.0.0', port=5003) 