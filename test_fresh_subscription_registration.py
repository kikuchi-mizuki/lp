#!/usr/bin/env python3
"""
新しいサブスクリプション登録のテストスクリプト
データベースがクリアされた状態から、最初からサブスクリプション登録をテスト
"""

import os
import sys
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# プロジェクトのルートディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
lp_dir = os.path.join(current_dir, 'lp')
sys.path.append(lp_dir)

# 環境変数を正しく読み込む
os.chdir(lp_dir)

from utils.db import get_db_connection
import requests
import json

def test_fresh_subscription_registration():
    """新しいサブスクリプション登録のテスト"""
    print("=== 新しいサブスクリプション登録テスト ===")
    
    # 1. データベースの状態を確認
    print("\n1. データベースの状態を確認...")
    conn = get_db_connection()
    c = conn.cursor()
    
    # 各テーブルの件数を確認
    tables = ['users', 'companies', 'company_payments', 'usage_logs', 'user_states']
    for table in tables:
        try:
            c.execute(f'SELECT COUNT(*) FROM {table}')
            count = c.fetchone()[0]
            print(f"  - {table}: {count}件")
        except Exception as e:
            print(f"  - {table}: エラー - {e}")
    
    conn.close()
    
    # 2. LINE Webhookのテスト
    print("\n2. LINE Webhookのテスト...")
    
    # テスト用のLINEイベントデータ
    test_event = {
        "destination": "Uf2cd175a948c6b8bd6edef39ef29b37e",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "テストメッセージ"
                },
                "webhookEventId": "test_webhook_id",
                "deliveryContext": {
                    "isRedelivery": False
                },
                "timestamp": 1754429442849,
                "source": {
                    "type": "user",
                    "userId": "U1b9d0d75b0c770dc1107dde349d572f7"
                },
                "replyToken": "test_reply_token",
                "mode": "active"
            }
        ]
    }
    
    # LINE WebhookエンドポイントにPOSTリクエストを送信
    webhook_url = "https://lp-production-9e2c.up.railway.app/line/webhook"
    
    try:
        response = requests.post(
            webhook_url,
            json=test_event,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"  - Webhookレスポンス: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ LINE Webhookが正常に動作しています")
        else:
            print(f"  ❌ LINE Webhookエラー: {response.text}")
            
    except Exception as e:
        print(f"  ❌ LINE Webhook接続エラー: {e}")
    
    # 3. 新しいユーザー登録のテスト
    print("\n3. 新しいユーザー登録のテスト...")
    
    # テスト用のメールアドレス
    test_email = "test@example.com"
    
    # ユーザー登録のテスト
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 新しいユーザーを作成
        c.execute('''
            INSERT INTO users (email, stripe_customer_id, stripe_subscription_id, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            RETURNING id
        ''', (test_email, 'cus_test_123', 'sub_test_123'))
        
        user_id = c.fetchone()[0]
        print(f"  ✅ 新しいユーザーを作成: user_id={user_id}")
        
        # ユーザー情報を確認
        c.execute('SELECT id, email, line_user_id FROM users WHERE id = %s', (user_id,))
        user_info = c.fetchone()
        print(f"  - ユーザー情報: {user_info}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"  ❌ ユーザー登録エラー: {e}")
    
    # 4. サブスクリプション登録プロセスの説明
    print("\n4. サブスクリプション登録プロセス:")
    print("  📋 手順:")
    print("    1. LINEで「追加」と入力")
    print("    2. コンテンツ選択メニューが表示される")
    print("    3. 「1」「2」「3」のいずれかを選択")
    print("    4. 確認メッセージが表示される")
    print("    5. 「はい」でコンテンツを追加")
    print("    6. 企業登録フォームへのリンクが表示される")
    print("    7. 企業情報を入力してサブスクリプションを開始")
    
    print("\n  🔗 テスト用URL:")
    print("    - LINE Webhook: https://lp-production-9e2c.up.railway.app/line/webhook")
    print("    - 企業登録フォーム: https://lp-production-9e2c.up.railway.app/company-registration")
    
    print("\n  📱 テスト用LINEユーザーID:")
    print("    - U1b9d0d75b0c770dc1107dde349d572f7")
    
    print("\n  🎯 次のステップ:")
    print("    1. LINEで「追加」と入力してテスト開始")
    print("    2. コンテンツ選択から企業登録まで一連の流れをテスト")
    print("    3. 実際のStripeサブスクリプションを作成")
    print("    4. コンテンツ追加・解約・状態確認の全機能をテスト")

if __name__ == "__main__":
    test_fresh_subscription_registration() 