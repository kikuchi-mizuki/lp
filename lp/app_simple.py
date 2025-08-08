#!/usr/bin/env python3
"""
シンプルなテスト用Flaskアプリケーション
"""

from flask import Flask, jsonify
import os

# Flaskアプリケーションの作成
app = Flask(__name__)

@app.route('/')
def health_check():
    """ヘルスチェック"""
    return "OK", 200

@app.route('/ping')
def ping():
    """ping"""
    return "pong", 200

@app.route('/test')
def test():
    """テストエンドポイント"""
    return jsonify({
        'status': 'success',
        'message': 'Simple Flask app is working!'
    })

if __name__ == '__main__':
    # Railwayが提供する$PORTを最優先で使用
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=True, host='0.0.0.0', port=port)
