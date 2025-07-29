#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json

def test_line_auth():
    """LINE APIの認証テスト"""
    print("=== LINE API 認証テスト ===\n")
    
    # 環境変数の確認
    line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
    
    print(f"LINE_CHANNEL_ACCESS_TOKEN: {'設定済み' if line_channel_access_token else '未設定'}")
    if line_channel_access_token:
        print(f"トークン長: {len(line_channel_access_token)}文字")
        print(f"トークン先頭: {line_channel_access_token[:10]}...")
        print(f"トークン末尾: ...{line_channel_access_token[-10:]}")
    
    print(f"LINE_CHANNEL_SECRET: {'設定済み' if line_channel_secret else '未設定'}")
    
    if not line_channel_access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKENが設定されていません")
        return
    
    headers = {
        'Authorization': f'Bearer {line_channel_access_token}',
        'Content-Type': 'application/json'
    }
    
    # 1. プロフィール取得テスト（認証確認）
    print(f"\n📊 1. LINE API 認証テスト（プロフィール取得）:")
    try:
        response = requests.get('https://api.line.me/v2/bot/profile/U1b9d0d75b0c770dc1107dde349d572f7', headers=headers, timeout=10)
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
        if response.status_code == 200:
            print("✅ LINE API認証成功")
        elif response.status_code == 401:
            print("❌ LINE API認証エラー - トークンが無効")
        elif response.status_code == 404:
            print("⚠️ ユーザーが見つかりません（認証は成功）")
        else:
            print(f"⚠️ 予期しないレスポンス: {response.status_code}")
            
    except Exception as e:
        print(f"❌ LINE API接続エラー: {e}")
    
    # 2. ボット情報取得テスト
    print(f"\n📊 2. LINE API ボット情報取得テスト:")
    try:
        response = requests.get('https://api.line.me/v2/bot/info', headers=headers, timeout=10)
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
        if response.status_code == 200:
            print("✅ LINE API認証成功（ボット情報取得）")
        elif response.status_code == 401:
            print("❌ LINE API認証エラー - トークンが無効")
        else:
            print(f"⚠️ 予期しないレスポンス: {response.status_code}")
            
    except Exception as e:
        print(f"❌ LINE API接続エラー: {e}")

def test_reply_token():
    """replyTokenのテスト"""
    print(f"\n=== replyToken テスト ===\n")
    
    line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    if not line_channel_access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKENが設定されていません")
        return
    
    headers = {
        'Authorization': f'Bearer {line_channel_access_token}',
        'Content-Type': 'application/json'
    }
    
    # 無効なreplyTokenでテスト
    test_cases = [
        {
            'name': '空のreplyToken',
            'data': {
                'replyToken': '',
                'messages': [{'type': 'text', 'text': 'テスト'}]
            }
        },
        {
            'name': '無効なreplyToken',
            'data': {
                'replyToken': 'invalid_token',
                'messages': [{'type': 'text', 'text': 'テスト'}]
            }
        },
        {
            'name': '長すぎるreplyToken',
            'data': {
                'replyToken': 'a' * 1000,
                'messages': [{'type': 'text', 'text': 'テスト'}]
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"📊 {test_case['name']}:")
        try:
            response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=test_case['data'], timeout=10)
            print(f"  ステータスコード: {response.status_code}")
            print(f"  レスポンス: {response.text}")
        except Exception as e:
            print(f"  ❌ エラー: {e}")

if __name__ == "__main__":
    test_line_auth()
    test_reply_token() 