#!/usr/bin/env python3
"""
Webhookエラー詳細調査・診断スクリプト
"""

import os
import requests
import json
import time
from utils.db import get_db_connection

def debug_webhook_errors():
    """Webhookエラーの詳細を調査"""
    try:
        print("=== Webhookエラー詳細調査 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 現在のWebhook URL設定を確認
        print("\n1. 現在のWebhook URL設定確認")
        c.execute('''
            SELECT c.id, c.company_name, cla.webhook_url, cla.line_channel_id
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
        ''')
        
        companies = c.fetchall()
        
        for company_id, company_name, webhook_url, line_channel_id in companies:
            print(f"\n🔍 企業: {company_name}")
            print(f"  Webhook URL: {webhook_url}")
            print(f"  LINEチャネルID: {line_channel_id}")
            
            # 2. Webhook URLの接続テスト
            if webhook_url:
                print(f"  🔄 Webhook URL接続テスト中...")
                
                try:
                    # HEADリクエストで接続確認
                    response = requests.head(webhook_url, timeout=10)
                    print(f"    ステータスコード: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"    ✅ Webhook URLに接続可能")
                    elif response.status_code == 405:
                        print(f"    ⚠️ Method Not Allowed (POSTのみ許可)")
                    else:
                        print(f"    ❌ 接続エラー: {response.status_code}")
                        
                except requests.exceptions.ConnectionError:
                    print(f"    ❌ 接続エラー: サーバーに到達できません")
                except requests.exceptions.Timeout:
                    print(f"    ❌ タイムアウトエラー: 応答がありません")
                except Exception as e:
                    print(f"    ❌ 予期しないエラー: {e}")
        
        # 3. 環境変数の確認
        print(f"\n2. 環境変数確認")
        
        env_vars = [
            'LINE_CHANNEL_SECRET',
            'LINE_CHANNEL_ACCESS_TOKEN',
            'STRIPE_WEBHOOK_SECRET',
            'DATABASE_URL',
            'BASE_URL',
            'BASE_DOMAIN'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # 機密情報は一部マスク
                if 'SECRET' in var or 'TOKEN' in var:
                    masked_value = value[:8] + '***' if len(value) > 8 else '***'
                    print(f"  ✅ {var}: {masked_value}")
                else:
                    print(f"  ✅ {var}: {value}")
            else:
                print(f"  ❌ {var}: 未設定")
        
        # 4. LINE Developers Console設定の確認
        print(f"\n3. LINE Developers Console設定確認")
        
        line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        if line_channel_secret:
            print(f"  ✅ LINE_CHANNEL_SECRET: 設定済み")
            
            # LINE Developers Consoleの設定を確認
            print(f"  📋 LINE Developers Consoleで確認すべき項目:")
            print(f"     - Webhook URL: {webhook_url if webhook_url else '未設定'}")
            print(f"     - Webhook利用: 有効")
            print(f"     - 検証: 成功")
            print(f"     - 署名検証: 有効")
        else:
            print(f"  ❌ LINE_CHANNEL_SECRET: 未設定")
        
        # 5. アプリケーションのWebhookエンドポイント確認
        print(f"\n4. アプリケーションWebhookエンドポイント確認")
        
        base_url = os.getenv('BASE_URL', 'https://lp-production-9e2c.up.railway.app')
        
        webhook_endpoints = [
            f"{base_url}/line/webhook",
            f"{base_url}/stripe/webhook",
            f"{base_url}/webhook/{company_id}" if company_id else None
        ]
        
        for endpoint in webhook_endpoints:
            if endpoint:
                print(f"  🔄 エンドポイント確認: {endpoint}")
                
                try:
                    response = requests.head(endpoint, timeout=10)
                    print(f"    ステータスコード: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"    ✅ エンドポイント利用可能")
                    elif response.status_code == 405:
                        print(f"    ⚠️ Method Not Allowed (POSTのみ)")
                    else:
                        print(f"    ❌ エラー: {response.status_code}")
                        
                except Exception as e:
                    print(f"    ❌ 接続エラー: {e}")
        
        # 6. データベースのWebhook関連テーブル確認
        print(f"\n5. データベースWebhook関連テーブル確認")
        
        # company_line_accountsテーブルの確認
        c.execute('''
            SELECT COUNT(*) as count, 
                   COUNT(CASE WHEN webhook_url IS NOT NULL THEN 1 END) as with_webhook,
                   COUNT(CASE WHEN webhook_url IS NULL THEN 1 END) as without_webhook
            FROM company_line_accounts
        ''')
        
        webhook_stats = c.fetchone()
        print(f"  📊 company_line_accounts:")
        print(f"    総レコード数: {webhook_stats[0]}")
        print(f"    Webhook URL設定済み: {webhook_stats[1]}")
        print(f"    Webhook URL未設定: {webhook_stats[2]}")
        
        # 7. エラーログの確認（可能な場合）
        print(f"\n6. エラーログ確認")
        
        # 最近のWebhook関連のエラーを確認
        c.execute('''
            SELECT id, company_id, deployment_status, deployment_log, created_at
            FROM company_deployments
            WHERE deployment_status = 'error' OR deployment_log LIKE '%webhook%'
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        
        error_logs = c.fetchall()
        
        if error_logs:
            print(f"  📋 最近のWebhook関連エラー:")
            for log_id, comp_id, status, log, created in error_logs:
                print(f"    ID: {log_id}, 企業ID: {comp_id}, ステータス: {status}")
                print(f"    ログ: {log[:100]}..." if log else "ログなし")
                print(f"    作成日時: {created}")
        else:
            print(f"  ✅ Webhook関連のエラーログはありません")
        
        conn.close()
        
        # 8. 推奨修正手順
        print(f"\n7. 推奨修正手順")
        print(f"  🔧 Webhookエラー修正手順:")
        print(f"    1. LINE Developers ConsoleでWebhook URLを確認")
        print(f"    2. Webhook URLの検証を実行")
        print(f"    3. 署名検証の設定を確認")
        print(f"    4. 環境変数の設定を確認")
        print(f"    5. アプリケーションのログを確認")
        print(f"    6. データベースの接続を確認")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhookエラー調査エラー: {e}")
        return False

def test_webhook_connection(webhook_url):
    """Webhook URLの接続テスト"""
    try:
        print(f"\n=== Webhook URL接続テスト ===")
        print(f"テスト対象: {webhook_url}")
        
        # 1. HEADリクエストで接続確認
        print(f"1. HEADリクエスト...")
        response = requests.head(webhook_url, timeout=10)
        print(f"   ステータスコード: {response.status_code}")
        print(f"   レスポンスヘッダー: {dict(response.headers)}")
        
        # 2. POSTリクエストでWebhookテスト
        print(f"2. POSTリクエスト...")
        
        # テスト用のWebhookペイロード
        test_payload = {
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "text": "test"
                    },
                    "replyToken": "test_token",
                    "source": {
                        "userId": "test_user",
                        "type": "user"
                    }
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Line-Signature': 'test_signature'
        }
        
        response = requests.post(webhook_url, json=test_payload, headers=headers, timeout=10)
        print(f"   ステータスコード: {response.status_code}")
        print(f"   レスポンス: {response.text[:200]}...")
        
        if response.status_code == 200:
            print(f"   ✅ Webhook接続テスト成功")
            return True
        else:
            print(f"   ❌ Webhook接続テスト失敗")
            return False
            
    except Exception as e:
        print(f"   ❌ Webhook接続テストエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("Webhookエラー詳細調査を開始します...")
    
    # 1. 全体的な調査
    if debug_webhook_errors():
        print("\n✅ Webhookエラー調査が完了しました")
        
        # 2. 特定のWebhook URLの接続テスト
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT webhook_url FROM company_line_accounts WHERE webhook_url IS NOT NULL LIMIT 1')
        result = c.fetchone()
        conn.close()
        
        if result and result[0]:
            webhook_url = result[0]
            print(f"\n🔄 特定のWebhook URL接続テストを実行中...")
            test_webhook_connection(webhook_url)
        else:
            print(f"\n⚠️ テスト対象のWebhook URLが見つかりません")
    else:
        print("\n❌ Webhookエラー調査に失敗しました")

if __name__ == "__main__":
    main() 