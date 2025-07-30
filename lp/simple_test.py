#!/usr/bin/env python3
"""
簡単なテスト用スクリプト
Flaskサーバーの起動とテストを分離
"""

import requests
import time
import subprocess
import sys
import os

def start_flask_server():
    """Flaskサーバーを起動"""
    print("🚀 Flaskサーバーを起動中...")
    
    # バックグラウンドでFlaskサーバーを起動
    process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"✅ Flaskサーバーが起動しました (PID: {process.pid})")
    return process

def test_server_connection():
    """サーバー接続をテスト"""
    print("🔍 サーバー接続をテスト中...")
    
    try:
        # ヘルスチェック
        response = requests.get("http://127.0.0.1:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ サーバー接続成功!")
            return True
        else:
            print(f"❌ サーバー応答エラー: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ サーバー接続失敗: {e}")
        return False

def test_line_api():
    """LINE APIをテスト"""
    print("🔍 LINE APIをテスト中...")
    
    try:
        # LINE API ヘルスチェック
        response = requests.get("http://127.0.0.1:5000/api/v1/line/health", timeout=5)
        if response.status_code == 200:
            print("✅ LINE API接続成功!")
            print(f"   レスポンス: {response.json()}")
            return True
        else:
            print(f"❌ LINE API応答エラー: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ LINE API接続失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("=== 簡単なテストスクリプト ===")
    
    # Flaskサーバーを起動
    server_process = start_flask_server()
    
    # サーバー起動を待つ
    print("⏳ サーバー起動を待機中...")
    time.sleep(5)
    
    # サーバー接続をテスト
    if test_server_connection():
        # LINE APIをテスト
        test_line_api()
    else:
        print("❌ サーバー接続に失敗しました")
    
    # サーバーを停止
    print("🛑 サーバーを停止中...")
    server_process.terminate()
    server_process.wait()
    print("✅ サーバーが停止しました")

if __name__ == "__main__":
    main() 