#!/usr/bin/env python3
"""
LINE Webhookの処理を詳しく調べるデバッグスクリプト
"""

import requests
import json
import time

def test_line_webhook_simulation():
    """LINE Webhookの処理をシミュレート"""
    
    print("🔍 LINE Webhook処理のデバッグ")
    print("=" * 50)
    
    # テスト用のLINEユーザーID（実際のユーザーIDに変更してください）
    test_line_user_id = "U231cdb3fc0687f3abc7bcaba5214dfff"
    
    print(f"テストユーザーID: {test_line_user_id}")
    
    # 1. データベースでのユーザー検索をシミュレート
    print("\n📊 ステップ1: データベースでのユーザー検索")
    try:
        response = requests.get(f"https://lp-production-9e2c.up.railway.app/debug/user/{test_line_user_id}")
        if response.status_code == 200:
            user_data = response.json()
            print("✅ ユーザー情報取得成功:")
            print(f"   - データベースID: {user_data['database_check'].get('user_id')}")
            print(f"   - メールアドレス: {user_data['database_check'].get('email')}")
            print(f"   - LINEユーザーID: {user_data['database_check'].get('line_user_id')}")
            print(f"   - StripeサブスクリプションID: {user_data['database_check'].get('stripe_subscription_id')}")
            print(f"   - 決済状況: {user_data['payment_check'].get('is_paid')}")
            print(f"   - サブスクリプション状態: {user_data['payment_check'].get('subscription_status')}")
        else:
            print(f"❌ ユーザー情報取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ユーザー情報取得エラー: {e}")
    
    # 2. LINE APIの状態確認
    print("\n💬 ステップ2: LINE APIの状態確認")
    try:
        response = requests.get("https://lp-production-9e2c.up.railway.app/line/status")
        if response.status_code == 200:
            line_status = response.json()
            print(f"✅ LINE API状態: {line_status}")
        else:
            print(f"❌ LINE API状態取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ LINE API状態取得エラー: {e}")
    
    # 3. 最近のユーザー一覧確認
    print("\n👥 ステップ3: 最近のユーザー一覧")
    try:
        response = requests.get("https://lp-production-9e2c.up.railway.app/debug/users")
        if response.status_code == 200:
            users_data = response.json()
            print("✅ ユーザー一覧取得成功:")
            for user in users_data.get('users', []):
                print(f"   - ID: {user.get('id')}, メール: {user.get('email')}, LINE_ID: {user.get('line_user_id')}")
        else:
            print(f"❌ ユーザー一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ユーザー一覧取得エラー: {e}")

def check_specific_user_webhook(line_user_id):
    """特定のユーザーのWebhook処理を確認"""
    
    print(f"\n🔍 特定ユーザーのWebhook処理確認: {line_user_id}")
    print("=" * 50)
    
    # 1. ユーザーの詳細情報を取得
    try:
        response = requests.get(f"https://lp-production-9e2c.up.railway.app/debug/user/{line_user_id}")
        if response.status_code == 200:
            user_data = response.json()
            
            print("📊 ユーザー情報:")
            print(f"   - データベースに存在: {user_data['database_check'].get('found')}")
            print(f"   - 決済済み: {user_data['payment_check'].get('is_paid')}")
            print(f"   - サブスクリプション状態: {user_data['payment_check'].get('subscription_status')}")
            
            if user_data['payment_check'].get('is_paid'):
                print("✅ このユーザーは決済済みとして判定されています")
                print("   問題: LINE Webhookの処理で何らかのエラーが発生している可能性があります")
            else:
                print("❌ このユーザーは決済済みとして判定されていません")
                print(f"   理由: {user_data['payment_check'].get('message')}")
                
        else:
            print(f"❌ ユーザー情報取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ユーザー情報取得エラー: {e}")

if __name__ == "__main__":
    # 基本的なWebhook処理の確認
    test_line_webhook_simulation()
    
    print("\n" + "="*60)
    print("特定のユーザーを確認する場合は、以下のように実行してください:")
    print("python debug_line_webhook.py <LINE_USER_ID>")
    print("例: python debug_line_webhook.py U1234567890abcdef")
    
    # コマンドライン引数がある場合は特定ユーザーを確認
    import sys
    if len(sys.argv) > 1:
        line_user_id = sys.argv[1]
        check_specific_user_webhook(line_user_id) 