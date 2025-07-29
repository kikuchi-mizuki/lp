#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json

def test_line_api():
    """LINE APIの設定と接続をテスト"""
    print("=== LINE API 設定テスト ===\n")
    
    # 環境変数の確認
    line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
    
    print(f"LINE_CHANNEL_ACCESS_TOKEN: {'設定済み' if line_channel_access_token else '未設定'}")
    print(f"LINE_CHANNEL_SECRET: {'設定済み' if line_channel_secret else '未設定'}")
    
    if not line_channel_access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKENが設定されていません")
        return
    
    # LINE APIのプロフィール取得テスト
    headers = {
        'Authorization': f'Bearer {line_channel_access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # プロフィール取得APIでテスト
        response = requests.get('https://api.line.me/v2/bot/profile/U1b9d0d75b0c770dc1107dde349d572f7', headers=headers)
        
        print(f"\n📊 LINE API プロフィール取得テスト:")
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
        if response.status_code == 200:
            print("✅ LINE API接続成功")
        else:
            print(f"❌ LINE API接続失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ LINE API接続エラー: {e}")
    
    # メッセージ送信APIのテスト（ダミーデータ）
    print(f"\n📊 LINE API メッセージ送信テスト:")
    
    test_data = {
        'replyToken': 'test_reply_token',
        'messages': [
            {
                'type': 'text',
                'text': 'テストメッセージ'
            }
        ]
    }
    
    try:
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=test_data)
        
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
        if response.status_code == 400:
            print("✅ LINE API接続は成功（400エラーは予想通り - 無効なreplyToken）")
        elif response.status_code == 401:
            print("❌ LINE API認証エラー - トークンが無効")
        else:
            print(f"⚠️ 予期しないレスポンス: {response.status_code}")
            
    except Exception as e:
        print(f"❌ LINE API接続エラー: {e}")

def test_line_webhook():
    """LINE Webhookの設定確認"""
    print(f"\n=== LINE Webhook 設定確認 ===\n")
    
    # RailwayのURLを確認
    railway_url = os.getenv('RAILWAY_STATIC_URL')
    if railway_url:
        webhook_url = f"{railway_url}/line/webhook"
        print(f"Webhook URL: {webhook_url}")
    else:
        print("⚠️ RAILWAY_STATIC_URLが設定されていません")
        print("Webhook URL: https://lp-production-9e2c.up.railway.app/line/webhook")

if __name__ == "__main__":
    test_line_api()
    test_line_webhook() 