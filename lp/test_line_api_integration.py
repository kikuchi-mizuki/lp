#!/usr/bin/env python3
"""
LINE API統合テストスクリプト
企業のLINEアカウント作成・メッセージ送信機能をテスト
"""

import requests
import json
import time

def test_line_api_integration():
    """LINE API統合テスト"""
    print("=== LINE API統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # テスト企業ID（既存の企業を使用）
    test_company_id = 1
    
    print(f"🔗 テスト対象企業ID: {test_company_id}")
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. LINE API ヘルスチェック
    print(f"\n📋 1. LINE API ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/line/health")
        if response.status_code == 200:
            print(f"  ✅ ヘルスチェック成功: {response.json()}")
        else:
            print(f"  ❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. LINEチャンネル作成
    print(f"\n📋 2. LINEチャンネル作成テスト")
    try:
        response = requests.post(f"{base_url}/api/v1/line/companies/{test_company_id}/create-channel")
        if response.status_code == 201:
            result = response.json()
            print(f"  ✅ チャンネル作成成功: {result['message']}")
            print(f"     LINEアカウントID: {result['line_account_id']}")
            print(f"     チャンネルID: {result['credentials']['channel_id']}")
            print(f"     Basic ID: {result['credentials']['basic_id']}")
        else:
            print(f"  ❌ チャンネル作成失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ チャンネル作成エラー: {e}")
    
    # 3. LINEメッセージ送信テスト
    print(f"\n📋 3. LINEメッセージ送信テスト")
    try:
        test_message = "🚀 企業管理システムからのテストメッセージです！\n\n✅ LINE API連携が正常に動作しています。\n📅 送信日時: " + time.strftime("%Y-%m-%d %H:%M:%S")
        
        payload = {
            "message": test_message,
            "type": "text"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/line/companies/{test_company_id}/send-message",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ メッセージ送信成功: {result['message']}")
            print(f"     チャンネルID: {result['channel_id']}")
        else:
            print(f"  ❌ メッセージ送信失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ メッセージ送信エラー: {e}")
    
    # 4. LINE統計情報取得テスト
    print(f"\n📋 4. LINE統計情報取得テスト")
    try:
        response = requests.get(f"{base_url}/api/v1/line/companies/{test_company_id}/statistics")
        if response.status_code == 200:
            result = response.json()
            stats = result['statistics']
            print(f"  ✅ 統計情報取得成功:")
            print(f"     チャンネルID: {stats['channel_id']}")
            print(f"     Basic ID: {stats['basic_id']}")
            print(f"     ステータス: {stats['status']}")
            print(f"     メッセージ数: {stats['message_count']}")
            print(f"     フォロワー数: {stats['followers_count']}")
        else:
            print(f"  ❌ 統計情報取得失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ 統計情報取得エラー: {e}")
    
    # 5. 通知送信テスト
    print(f"\n📋 5. 通知送信テスト")
    notification_types = [
        ("payment_completion", "月額プラン 2,980円の支払いが完了しました"),
        ("subscription_renewal", "契約が正常に更新されました"),
        ("trial_expiring", "トライアル期間が3日後に終了します"),
        ("system_maintenance", "システムメンテナンスを実施します")
    ]
    
    for notification_type, message in notification_types:
        try:
            payload = {
                "type": notification_type,
                "message": message
            }
            
            response = requests.post(
                f"{base_url}/api/v1/line/companies/{test_company_id}/notify",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ {notification_type}通知成功: {result['message']}")
            else:
                print(f"  ❌ {notification_type}通知失敗: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {notification_type}通知エラー: {e}")
    
    # 6. 全LINEアカウント情報取得テスト
    print(f"\n📋 6. 全LINEアカウント情報取得テスト")
    try:
        response = requests.get(f"{base_url}/api/v1/line/accounts")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ 全アカウント情報取得成功:")
            print(f"     総アカウント数: {result['total_count']}")
            
            for account in result['accounts']:
                print(f"     - {account['company_name']}: {account['basic_id']} ({account['status']})")
        else:
            print(f"  ❌ 全アカウント情報取得失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ 全アカウント情報取得エラー: {e}")
    
    # 7. Webhook設定テスト
    print(f"\n📋 7. Webhook設定テスト")
    try:
        webhook_url = f"https://your-domain.com/webhook/company-{test_company_id}"
        payload = {
            "webhook_url": webhook_url
        }
        
        response = requests.post(
            f"{base_url}/api/v1/line/companies/{test_company_id}/webhook",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Webhook設定成功: {result['message']}")
        else:
            print(f"  ❌ Webhook設定失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ Webhook設定エラー: {e}")
    
    # 8. LINEアカウント無効化・有効化テスト
    print(f"\n📋 8. LINEアカウント無効化・有効化テスト")
    
    # 無効化
    try:
        response = requests.post(f"{base_url}/api/v1/line/companies/{test_company_id}/disable")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ アカウント無効化成功: {result['message']}")
        else:
            print(f"  ❌ アカウント無効化失敗: {response.status_code}")
    except Exception as e:
        print(f"  ❌ アカウント無効化エラー: {e}")
    
    # 有効化
    try:
        response = requests.post(f"{base_url}/api/v1/line/companies/{test_company_id}/enable")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ アカウント有効化成功: {result['message']}")
        else:
            print(f"  ❌ アカウント有効化失敗: {response.status_code}")
    except Exception as e:
        print(f"  ❌ アカウント有効化エラー: {e}")
    
    print(f"\n🎉 LINE API統合テスト完了！")
    print(f"💡 次のステップ:")
    print(f"   1. 実際のLINE Developers Consoleでチャンネルを作成")
    print(f"   2. 本物のLINE Messaging APIを使用")
    print(f"   3. Webhook URLを実際のドメインに設定")
    print(f"   4. 企業ごとの通知機能を実装")
    
    return True

def test_line_api_with_real_data():
    """実際のデータを使用したLINE APIテスト"""
    print(f"\n=== 実際のデータを使用したLINE APIテスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 企業一覧を取得
    try:
        response = requests.get(f"{base_url}/api/v1/companies")
        if response.status_code == 200:
            companies = response.json()
            print(f"📋 利用可能な企業数: {len(companies)}")
            
            for company in companies[:3]:  # 最初の3社でテスト
                company_id = company['id']
                company_name = company['company_name']
                
                print(f"\n🏢 企業: {company_name} (ID: {company_id})")
                
                # LINEチャンネル作成
                response = requests.post(f"{base_url}/api/v1/line/companies/{company_id}/create-channel")
                if response.status_code == 201:
                    print(f"  ✅ LINEチャンネル作成成功")
                    
                    # テストメッセージ送信
                    payload = {
                        "message": f"🎉 {company_name}様、LINE連携が完了しました！",
                        "type": "text"
                    }
                    
                    response = requests.post(
                        f"{base_url}/api/v1/line/companies/{company_id}/send-message",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        print(f"  ✅ テストメッセージ送信成功")
                    else:
                        print(f"  ❌ テストメッセージ送信失敗")
                else:
                    print(f"  ❌ LINEチャンネル作成失敗")
        else:
            print(f"❌ 企業一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 実際データテストエラー: {e}")

if __name__ == "__main__":
    print("🚀 LINE API統合テストを開始します...")
    print("注意: Flaskサーバーが起動していることを確認してください")
    print("サーバー起動方法: python app.py")
    print()
    
    # 基本テスト
    success = test_line_api_integration()
    
    if success:
        # 実際のデータを使用したテスト
        test_line_api_with_real_data()
    
    print(f"\n✅ テスト完了！") 