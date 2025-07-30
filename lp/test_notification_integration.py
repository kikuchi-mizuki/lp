#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知・アラート機能統合テスト
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_notification_integration():
    """通知・アラート機能統合テスト"""
    print("=== 通知・アラート機能統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # テスト企業ID（既存の企業を使用）
    test_company_id = 1
    
    print(f"🔗 テスト対象企業ID: {test_company_id}")
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. 通知・アラートAPI ヘルスチェック
    print("\n1️⃣ 通知・アラートAPI ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/notification/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェック成功: {result['message']}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. 通知タイプ一覧取得
    print("\n2️⃣ 通知タイプ一覧取得")
    try:
        response = requests.get(f"{base_url}/api/v1/notification/types", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 通知タイプ取得成功: {len(result['notification_types'])}件")
            for notification_type, info in result['notification_types'].items():
                print(f"   - {notification_type}: {info['name']}")
        else:
            print(f"❌ 通知タイプ取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 通知タイプ取得エラー: {e}")
    
    # 3. 通知履歴取得
    print("\n3️⃣ 通知履歴取得")
    try:
        response = requests.get(f"{base_url}/api/v1/notification/history", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 通知履歴取得成功: {result['count']}件")
            for notification in result['notifications'][:3]:  # 最新3件を表示
                print(f"   - {notification['notification_type']}: {notification['sent_at']}")
        else:
            print(f"❌ 通知履歴取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 通知履歴取得エラー: {e}")
    
    # 4. 通知統計取得
    print("\n4️⃣ 通知統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/notification/statistics", timeout=10)
        if response.status_code == 200:
            result = response.json()
            stats = result['statistics']
            print(f"✅ 通知統計取得成功:")
            print(f"   - 今日の通知数: {stats['today_count']}件")
            print(f"   - 通知タイプ別統計: {len(stats['type_stats'])}件")
            print(f"   - 企業別統計: {len(stats['company_stats'])}件")
        else:
            print(f"❌ 通知統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 通知統計取得エラー: {e}")
    
    # 5. テスト通知送信
    print("\n5️⃣ テスト通知送信")
    try:
        test_data = {
            'notification_type': 'payment_success',
            'payment_data': {
                'next_billing_date': '2024年8月30日',
                'amount': 3900
            }
        }
        response = requests.post(
            f"{base_url}/api/v1/notification/companies/{test_company_id}/test-notification",
            json=test_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ テスト通知送信成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ テスト通知送信結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ テスト通知送信エラー: {e}")
    
    # 6. トライアル終了リマインダー
    print("\n6️⃣ トライアル終了リマインダー")
    try:
        reminder_data = {
            'days_before': 3
        }
        response = requests.post(
            f"{base_url}/api/v1/notification/companies/{test_company_id}/trial-reminder",
            json=reminder_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ トライアルリマインダー成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ トライアルリマインダー結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ トライアルリマインダーエラー: {e}")
    
    # 7. 契約更新リマインダー
    print("\n7️⃣ 契約更新リマインダー")
    try:
        reminder_data = {
            'days_before': 7
        }
        response = requests.post(
            f"{base_url}/api/v1/notification/companies/{test_company_id}/renewal-reminder",
            json=reminder_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 契約更新リマインダー成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ 契約更新リマインダー結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 契約更新リマインダーエラー: {e}")
    
    # 8. データ削除リマインダー
    print("\n8️⃣ データ削除リマインダー")
    try:
        reminder_data = {
            'days_before': 7
        }
        response = requests.post(
            f"{base_url}/api/v1/notification/companies/{test_company_id}/deletion-reminder",
            json=reminder_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ データ削除リマインダー成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ データ削除リマインダー結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ データ削除リマインダーエラー: {e}")
    
    # 9. 一括リマインダー送信
    print("\n9️⃣ 一括リマインダー送信")
    try:
        bulk_data = {
            'reminder_types': ['trial', 'renewal', 'deletion']
        }
        response = requests.post(
            f"{base_url}/api/v1/notification/companies/{test_company_id}/bulk-reminders",
            json=bulk_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 一括リマインダー成功:")
            for reminder_type, reminder_result in result['results'].items():
                status = "✅" if reminder_result['success'] else "❌"
                print(f"   - {reminder_type}: {status}")
        else:
            result = response.json()
            print(f"⚠️ 一括リマインダー結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 一括リマインダーエラー: {e}")
    
    print("\n🎉 通知・アラート機能統合テスト完了")
    return True

def test_notification_with_real_data():
    """実際のデータを使用した通知テスト"""
    print("\n=== 実際のデータを使用した通知テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 既存の企業を取得
    try:
        response = requests.get(f"{base_url}/api/v1/companies", timeout=10)
        if response.status_code == 200:
            companies = response.json()['companies']
            if companies:
                test_company = companies[0]
                test_company_id = test_company['id']
                
                print(f"🔗 テスト対象企業: {test_company['company_name']} (ID: {test_company_id})")
                
                # 支払い情報を確認
                response = requests.get(f"{base_url}/api/v1/stripe/companies/{test_company_id}/payment-status", timeout=10)
                if response.status_code == 200:
                    payment_status = response.json()
                    print(f"📊 支払い状況:")
                    print(f"   - ステータス: {payment_status.get('subscription_status', '不明')}")
                    print(f"   - 支払い状況: {payment_status.get('is_paid', False)}")
                    
                    # 支払い完了通知をテスト
                    if payment_status.get('is_paid'):
                        print("✅ 支払い完了通知をテストします")
                        test_payment_success_notification(test_company_id)
                    else:
                        print("⚠️ 支払い未完了のため、支払い失敗通知をテストします")
                        test_payment_failed_notification(test_company_id)
                else:
                    print("❌ 支払い状況確認に失敗しました")
            else:
                print("❌ テスト可能な企業が見つかりません")
        else:
            print("❌ 企業一覧取得に失敗しました")
    except Exception as e:
        print(f"❌ 企業取得エラー: {e}")

def test_payment_success_notification(company_id):
    """支払い完了通知のテスト"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        notification_data = {
            'notification_type': 'payment_success',
            'payment_data': {
                'next_billing_date': '2024年8月30日',
                'amount': 3900
            }
        }
        
        response = requests.post(
            f"{base_url}/api/v1/notification/companies/{company_id}/send",
            json=notification_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 支払い完了通知送信成功: {result['message']}")
        else:
            result = response.json()
            print(f"❌ 支払い完了通知送信失敗: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 支払い完了通知テストエラー: {e}")

def test_payment_failed_notification(company_id):
    """支払い失敗通知のテスト"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        notification_data = {
            'notification_type': 'payment_failed',
            'payment_data': {
                'amount': 3900,
                'retry_date': '2024年8月5日'
            }
        }
        
        response = requests.post(
            f"{base_url}/api/v1/notification/companies/{company_id}/send",
            json=notification_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 支払い失敗通知送信成功: {result['message']}")
        else:
            result = response.json()
            print(f"❌ 支払い失敗通知送信失敗: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 支払い失敗通知テストエラー: {e}")

def main():
    """メイン関数"""
    print("🚀 通知・アラート機能テストを開始します")
    
    # 基本的な統合テスト
    if test_notification_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return
    
    # 実際のデータを使用したテスト
    test_notification_with_real_data()

if __name__ == "__main__":
    main() 