#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json

def check_railway_logs():
    """Railway環境でのエラーログを確認"""
    print("=== Railway エラーログ確認 ===\n")
    
    # Railwayの環境変数を確認
    railway_url = os.getenv('RAILWAY_STATIC_URL', 'https://lp-production-9e2c.up.railway.app')
    
    try:
        # エラーログエンドポイントにアクセス
        response = requests.get(f"{railway_url}/error_log", timeout=10)
        
        if response.status_code == 200:
            print("📊 エラーログ内容:")
            print(response.text)
        else:
            print(f"❌ エラーログ取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ エラーログ確認エラー: {e}")

def test_line_webhook():
    """LINE Webhookの動作確認"""
    print(f"\n=== LINE Webhook 動作確認 ===\n")
    
    railway_url = os.getenv('RAILWAY_STATIC_URL', 'https://lp-production-9e2c.up.railway.app')
    webhook_url = f"{railway_url}/line/webhook"
    
    # テスト用のLINE Webhookイベント
    test_event = {
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "text": "テスト"
                },
                "replyToken": "test_reply_token",
                "source": {
                    "userId": "test_user_id",
                    "type": "user"
                }
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=test_event, timeout=10)
        print(f"📊 Webhookテスト結果:")
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
    except Exception as e:
        print(f"❌ Webhookテストエラー: {e}")

if __name__ == "__main__":
    check_railway_logs()
    test_line_webhook() 