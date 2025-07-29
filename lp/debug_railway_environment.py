#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time

def debug_railway_environment():
    """Railway環境での詳細デバッグ"""
    print("=== Railway 環境詳細デバッグ ===\n")
    
    # 環境変数の確認
    env_vars = [
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_CHANNEL_SECRET',
        'DATABASE_URL',
        'RAILWAY_DATABASE_URL',
        'RAILWAY_STATIC_URL',
        'STRIPE_SECRET_KEY'
    ]
    
    print("📊 環境変数確認:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var or 'SECRET' in var or 'KEY' in var:
                print(f"  {var}: 設定済み ({len(value)}文字)")
                print(f"    先頭: {value[:10]}...")
                print(f"    末尾: ...{value[-10:]}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: 未設定")
    
    # RailwayのURL確認
    railway_url = os.getenv('RAILWAY_STATIC_URL', 'https://lp-production-9e2c.up.railway.app')
    print(f"\n📊 Railway URL: {railway_url}")
    
    # ヘルスチェック
    try:
        response = requests.get(f"{railway_url}/health", timeout=10)
        print(f"📊 ヘルスチェック: {response.status_code}")
        if response.status_code == 200:
            print("✅ アプリケーションは正常に動作中")
        else:
            print(f"⚠️ アプリケーションに問題があります: {response.text}")
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")

def test_line_api_from_railway():
    """Railway環境からLINE APIをテスト"""
    print(f"\n=== Railway環境からLINE APIテスト ===\n")
    
    line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    if not line_channel_access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKENが設定されていません")
        return
    
    headers = {
        'Authorization': f'Bearer {line_channel_access_token}',
        'Content-Type': 'application/json'
    }
    
    # 1. ボット情報取得テスト
    print("📊 1. LINE API ボット情報取得テスト:")
    try:
        response = requests.get('https://api.line.me/v2/bot/info', headers=headers, timeout=10)
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
        if response.status_code == 200:
            print("✅ LINE API認証成功")
        elif response.status_code == 401:
            print("❌ LINE API認証エラー - トークンが無効")
        else:
            print(f"⚠️ 予期しないレスポンス: {response.status_code}")
            
    except Exception as e:
        print(f"❌ LINE API接続エラー: {e}")
    
    # 2. メッセージ送信APIのテスト（無効なreplyToken）
    print(f"\n📊 2. LINE API メッセージ送信テスト（無効なreplyToken）:")
    
    test_data = {
        'replyToken': 'invalid_reply_token_123',
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

def check_railway_logs():
    """Railway環境でのログ確認"""
    print(f"\n=== Railway ログ確認 ===\n")
    
    railway_url = os.getenv('RAILWAY_STATIC_URL', 'https://lp-production-9e2c.up.railway.app')
    
    # エラーログエンドポイントにアクセス
    try:
        response = requests.get(f"{railway_url}/error_log", timeout=10)
        print(f"📊 エラーログ取得: {response.status_code}")
        if response.status_code == 200:
            print("📄 エラーログ内容:")
            print(response.text)
        else:
            print(f"❌ エラーログ取得失敗: {response.text}")
    except Exception as e:
        print(f"❌ エラーログ確認エラー: {e}")

if __name__ == "__main__":
    debug_railway_environment()
    test_line_api_from_railway()
    check_railway_logs() 