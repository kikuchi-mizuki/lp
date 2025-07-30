#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動リマインダー機能統合テスト
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_reminder_integration():
    """自動リマインダー機能統合テスト"""
    print("=== 自動リマインダー機能統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. リマインダーAPI ヘルスチェック
    print("\n1️⃣ リマインダーAPI ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/reminder/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェック成功: {result['message']}")
            print(f"   - サービス状態: {result['service_status']}")
            print(f"   - 利用可能タイプ数: {result['available_types']}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. リマインダータイプ一覧取得
    print("\n2️⃣ リマインダータイプ一覧取得")
    try:
        response = requests.get(f"{base_url}/api/v1/reminder/types", timeout=10)
        if response.status_code == 200:
            result = response.json()
            reminder_types = result['reminder_types']
            print(f"✅ リマインダータイプ取得成功:")
            print(f"   - 利用可能タイプ数: {len(reminder_types)}")
            
            for reminder_type, type_info in reminder_types.items():
                print(f"   - {reminder_type}: {type_info['name']}")
                print(f"     * デフォルト日数: {type_info['default_days']}")
        else:
            print(f"❌ リマインダータイプ取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ リマインダータイプ取得エラー: {e}")
    
    # 3. 企業一覧を取得してテスト用の企業IDを取得
    print("\n3️⃣ テスト用企業情報取得")
    try:
        response = requests.get(f"{base_url}/api/v1/companies", timeout=10)
        if response.status_code == 200:
            result = response.json()
            companies = result['companies']
            
            if companies:
                test_company_id = companies[0]['id']
                test_company_name = companies[0]['name']
                print(f"✅ テスト企業取得成功:")
                print(f"   - 企業ID: {test_company_id}")
                print(f"   - 企業名: {test_company_name}")
            else:
                print("❌ テスト用の企業が見つかりません")
                return False
        else:
            print(f"❌ 企業一覧取得失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 企業一覧取得エラー: {e}")
        return False
    
    # 4. リマインダースケジュール作成
    print("\n4️⃣ リマインダースケジュール作成")
    try:
        schedule_data = {
            'reminder_type': 'trial_ending',
            'custom_days': [7, 3, 1],
            'custom_message': '⏰ トライアル終了のお知らせ\n\n📅 終了日: {trial_end_date}\n💰 開始金額: ¥{amount:,}\n\n💳 継続をご希望の場合は、お支払い方法の設定をお願いします。'
        }
        
        response = requests.post(
            f"{base_url}/api/v1/reminder/companies/{test_company_id}/schedules",
            json=schedule_data,
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            reminder = result['reminder']
            print(f"✅ リマインダースケジュール作成成功:")
            print(f"   - リマインダーID: {reminder['id']}")
            print(f"   - タイプ: {reminder['reminder_type']}")
            print(f"   - 名前: {reminder['reminder_name']}")
            print(f"   - ステータス: {reminder['status']}")
            
            reminder_id = reminder['id']
        else:
            print(f"❌ リマインダースケジュール作成失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ リマインダースケジュール作成エラー: {e}")
        return False
    
    # 5. リマインダースケジュール一覧取得
    print("\n5️⃣ リマインダースケジュール一覧取得")
    try:
        response = requests.get(f"{base_url}/api/v1/reminder/companies/{test_company_id}/schedules", timeout=10)
        if response.status_code == 200:
            result = response.json()
            reminders = result['reminders']
            print(f"✅ リマインダースケジュール一覧取得成功:")
            print(f"   - スケジュール数: {len(reminders)}件")
            
            for i, reminder in enumerate(reminders[:3]):
                print(f"   {i+1}. {reminder['reminder_name']} ({reminder['status']})")
        else:
            print(f"❌ リマインダースケジュール一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ リマインダースケジュール一覧取得エラー: {e}")
    
    # 6. リマインダー送信テスト
    print("\n6️⃣ リマインダー送信テスト")
    try:
        response = requests.post(
            f"{base_url}/api/v1/reminder/schedules/{reminder_id}/send",
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ リマインダー送信成功: {result['message']}")
            print(f"   - 送信時刻: {result['sent_at']}")
        else:
            print(f"❌ リマインダー送信失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ リマインダー送信エラー: {e}")
    
    # 7. ウェルカムリマインダー送信
    print("\n7️⃣ ウェルカムリマインダー送信")
    try:
        response = requests.post(
            f"{base_url}/api/v1/reminder/companies/{test_company_id}/send-welcome",
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ウェルカムリマインダー送信成功: {result['message']}")
        else:
            print(f"❌ ウェルカムリマインダー送信失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ウェルカムリマインダー送信エラー: {e}")
    
    # 8. トライアル終了リマインダー送信
    print("\n8️⃣ トライアル終了リマインダー送信")
    try:
        trial_data = {
            'days_before': 3
        }
        
        response = requests.post(
            f"{base_url}/api/v1/reminder/companies/{test_company_id}/send-trial-ending",
            json=trial_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ トライアル終了リマインダー送信成功: {result['message']}")
        else:
            print(f"❌ トライアル終了リマインダー送信失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ トライアル終了リマインダー送信エラー: {e}")
    
    # 9. 支払い期限リマインダー送信
    print("\n9️⃣ 支払い期限リマインダー送信")
    try:
        payment_data = {
            'days_before': 7
        }
        
        response = requests.post(
            f"{base_url}/api/v1/reminder/companies/{test_company_id}/send-payment-due",
            json=payment_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 支払い期限リマインダー送信成功: {result['message']}")
        else:
            print(f"❌ 支払い期限リマインダー送信失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 支払い期限リマインダー送信エラー: {e}")
    
    # 10. 契約更新リマインダー送信
    print("\n🔟 契約更新リマインダー送信")
    try:
        renewal_data = {
            'days_before': 14
        }
        
        response = requests.post(
            f"{base_url}/api/v1/reminder/companies/{test_company_id}/send-renewal",
            json=renewal_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 契約更新リマインダー送信成功: {result['message']}")
        else:
            print(f"❌ 契約更新リマインダー送信失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 契約更新リマインダー送信エラー: {e}")
    
    # 11. 利用状況リマインダー送信
    print("\n1️⃣1️⃣ 利用状況リマインダー送信")
    try:
        usage_data = {
            'days_before': 30
        }
        
        response = requests.post(
            f"{base_url}/api/v1/reminder/companies/{test_company_id}/send-usage",
            json=usage_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 利用状況リマインダー送信成功: {result['message']}")
        else:
            print(f"❌ 利用状況リマインダー送信失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 利用状況リマインダー送信エラー: {e}")
    
    # 12. 一括リマインダー送信
    print("\n1️⃣2️⃣ 一括リマインダー送信")
    try:
        bulk_data = {
            'reminder_types': ['welcome', 'trial_ending', 'payment_due']
        }
        
        response = requests.post(
            f"{base_url}/api/v1/reminder/companies/{test_company_id}/bulk-send",
            json=bulk_data,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 一括リマインダー送信成功: {result['message']}")
            print(f"   - 成功件数: {result['success_count']}/{result['total_count']}")
            
            for i, res in enumerate(result['results']):
                status_icon = "✅" if res['status'] == 'success' else "❌"
                print(f"   {i+1}. {res['reminder_type']}: {status_icon} {res['message']}")
        else:
            print(f"❌ 一括リマインダー送信失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 一括リマインダー送信エラー: {e}")
    
    # 13. リマインダー統計取得
    print("\n1️⃣3️⃣ リマインダー統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/reminder/statistics", timeout=10)
        if response.status_code == 200:
            result = response.json()
            statistics = result['statistics']
            print(f"✅ リマインダー統計取得成功:")
            print(f"   - 統計項目数: {len(statistics)}")
            
            for stat in statistics:
                print(f"   - {stat['reminder_type']}: 総数{stat['total_count']}, 送信済み{stat['sent_count']}")
        else:
            print(f"❌ リマインダー統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ リマインダー統計取得エラー: {e}")
    
    # 14. テストリマインダー送信
    print("\n1️⃣4️⃣ テストリマインダー送信")
    try:
        test_data = {
            'company_id': test_company_id,
            'reminder_type': 'welcome',
            'custom_message': '🎉 テスト用ウェルカムメッセージです！\n\n📅 テスト日時: {start_date}\n\n📱 何かご質問がございましたら、お気軽にお声かけください。'
        }
        
        response = requests.post(
            f"{base_url}/api/v1/reminder/test",
            json=test_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ テストリマインダー送信成功: {result['message']}")
        else:
            print(f"❌ テストリマインダー送信失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ テストリマインダー送信エラー: {e}")
    
    print("\n🎉 自動リマインダー機能統合テスト完了")
    return True

def test_reminder_with_real_data():
    """実際のデータを使用したリマインダーテスト"""
    print("\n=== 実際のデータを使用したリマインダーテスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 企業一覧を取得
    try:
        response = requests.get(f"{base_url}/api/v1/companies", timeout=10)
        if response.status_code == 200:
            result = response.json()
            companies = result['companies']
            
            if companies:
                print(f"📊 実際の企業データを使用したテスト:")
                print(f"   - 企業数: {len(companies)}")
                
                # 各企業に対してリマインダーをテスト
                for i, company in enumerate(companies[:3]):  # 最初の3社のみテスト
                    company_id = company['id']
                    company_name = company['name']
                    
                    print(f"\n🏢 企業 {i+1}: {company_name} (ID: {company_id})")
                    
                    # ウェルカムリマインダーを送信
                    try:
                        response = requests.post(
                            f"{base_url}/api/v1/reminder/companies/{company_id}/send-welcome",
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            print(f"   ✅ ウェルカムリマインダー送信成功")
                        else:
                            print(f"   ❌ ウェルカムリマインダー送信失敗")
                    except Exception as e:
                        print(f"   ❌ ウェルカムリマインダー送信エラー: {e}")
                    
                    # トライアル終了リマインダーを送信
                    try:
                        response = requests.post(
                            f"{base_url}/api/v1/reminder/companies/{company_id}/send-trial-ending",
                            json={'days_before': 3},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            print(f"   ✅ トライアル終了リマインダー送信成功")
                        else:
                            print(f"   ❌ トライアル終了リマインダー送信失敗")
                    except Exception as e:
                        print(f"   ❌ トライアル終了リマインダー送信エラー: {e}")
                    
                    time.sleep(1)  # リクエスト間隔を空ける
            else:
                print("❌ テスト用の企業が見つかりません")
        else:
            print(f"❌ 企業一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 実際のデータテストエラー: {e}")

def test_reminder_performance():
    """リマインダー機能パフォーマンステスト"""
    print("\n=== リマインダー機能パフォーマンステスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 各エンドポイントの応答時間を測定
    endpoints = [
        ('health', '/api/v1/reminder/health'),
        ('types', '/api/v1/reminder/types'),
        ('statistics', '/api/v1/reminder/statistics'),
        ('schedules', '/api/v1/reminder/schedules')
    ]
    
    performance_results = {}
    
    for name, endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ミリ秒
            
            if response.status_code == 200:
                print(f"✅ {name}: {response_time:.2f}ms")
                performance_results[name] = {
                    'status': 'success',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
            else:
                print(f"❌ {name}: {response.status_code} ({response_time:.2f}ms)")
                performance_results[name] = {
                    'status': 'error',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            print(f"❌ {name}: エラー ({str(e)})")
            performance_results[name] = {
                'status': 'exception',
                'error': str(e)
            }
    
    # パフォーマンスサマリー
    successful_requests = [r for r in performance_results.values() if r['status'] == 'success']
    if successful_requests:
        avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
        max_response_time = max(r['response_time'] for r in successful_requests)
        min_response_time = min(r['response_time'] for r in successful_requests)
        
        print(f"\n📊 パフォーマンスサマリー:")
        print(f"   - 成功リクエスト: {len(successful_requests)}/{len(endpoints)}")
        print(f"   - 平均応答時間: {avg_response_time:.2f}ms")
        print(f"   - 最大応答時間: {max_response_time:.2f}ms")
        print(f"   - 最小応答時間: {min_response_time:.2f}ms")

def main():
    """メイン関数"""
    print("🚀 自動リマインダー機能テストを開始します")
    
    # 基本的な統合テスト
    if test_reminder_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return
    
    # 実際のデータを使用したテスト
    test_reminder_with_real_data()
    
    # パフォーマンステスト
    test_reminder_performance()

if __name__ == "__main__":
    main() 