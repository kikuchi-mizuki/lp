#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time

def test_line_api_detailed():
    """LINE APIの詳細なテスト"""
    print("=== LINE API 詳細テスト ===\n")
    
    # 環境変数の確認
    line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
    
    print(f"LINE_CHANNEL_ACCESS_TOKEN: {'設定済み' if line_channel_access_token else '未設定'}")
    if line_channel_access_token:
        print(f"トークン長: {len(line_channel_access_token)}文字")
        print(f"トークン先頭: {line_channel_access_token[:10]}...")
    
    print(f"LINE_CHANNEL_SECRET: {'設定済み' if line_channel_secret else '未設定'}")
    
    if not line_channel_access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKENが設定されていません")
        return
    
    headers = {
        'Authorization': f'Bearer {line_channel_access_token}',
        'Content-Type': 'application/json'
    }
    
    # 1. プロフィール取得テスト
    print(f"\n📊 1. LINE API プロフィール取得テスト:")
    try:
        response = requests.get('https://api.line.me/v2/bot/profile/U1b9d0d75b0c770dc1107dde349d572f7', headers=headers, timeout=10)
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
        if response.status_code == 200:
            print("✅ LINE API接続成功")
        elif response.status_code == 401:
            print("❌ LINE API認証エラー - トークンが無効")
        else:
            print(f"⚠️ 予期しないレスポンス: {response.status_code}")
            
    except Exception as e:
        print(f"❌ LINE API接続エラー: {e}")
    
    # 2. メッセージ送信APIのテスト（無効なreplyToken）
    print(f"\n📊 2. LINE API メッセージ送信テスト（無効なreplyToken）:")
    
    test_data = {
        'replyToken': 'invalid_reply_token',
        'messages': [
            {
                'type': 'text',
                'text': 'テストメッセージ'
            }
        ]
    }
    
    try:
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=test_data, timeout=10)
        
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
    
    # 3. メッセージ送信APIのテスト（空のreplyToken）
    print(f"\n📊 3. LINE API メッセージ送信テスト（空のreplyToken）:")
    
    test_data_empty = {
        'replyToken': '',
        'messages': [
            {
                'type': 'text',
                'text': 'テストメッセージ'
            }
        ]
    }
    
    try:
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=test_data_empty, timeout=10)
        
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
    except Exception as e:
        print(f"❌ LINE API接続エラー: {e}")
    
    # 4. メッセージ送信APIのテスト（無効なメッセージ形式）
    print(f"\n📊 4. LINE API メッセージ送信テスト（無効なメッセージ形式）:")
    
    test_data_invalid = {
        'replyToken': 'test_reply_token',
        'messages': [
            {
                'type': 'invalid_type',
                'text': 'テストメッセージ'
            }
        ]
    }
    
    try:
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=test_data_invalid, timeout=10)
        
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
    except Exception as e:
        print(f"❌ LINE API接続エラー: {e}")

def test_railway_environment():
    """Railway環境の確認"""
    print(f"\n=== Railway 環境確認 ===\n")
    
    # Railwayの環境変数を確認
    railway_url = os.getenv('RAILWAY_STATIC_URL')
    database_url = os.getenv('DATABASE_URL')
    railway_database_url = os.getenv('RAILWAY_DATABASE_URL')
    
    print(f"RAILWAY_STATIC_URL: {'設定済み' if railway_url else '未設定'}")
    if railway_url:
        print(f"URL: {railway_url}")
    
    print(f"DATABASE_URL: {'設定済み' if database_url else '未設定'}")
    print(f"RAILWAY_DATABASE_URL: {'設定済み' if railway_database_url else '未設定'}")

if __name__ == "__main__":
    test_line_api_detailed()
    test_railway_environment() 