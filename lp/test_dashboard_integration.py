#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
管理ダッシュボード機能統合テスト
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_dashboard_integration():
    """管理ダッシュボード機能統合テスト"""
    print("=== 管理ダッシュボード機能統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. ダッシュボードAPI ヘルスチェック
    print("\n1️⃣ ダッシュボードAPI ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェック成功: {result['message']}")
            print(f"   - サービス状態: {result['service_status']}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. 概要統計取得
    print("\n2️⃣ 概要統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/overview", timeout=10)
        if response.status_code == 200:
            result = response.json()
            overview = result['overview']
            print(f"✅ 概要統計取得成功:")
            print(f"   - 企業数: {overview['companies']['total']}社")
            print(f"   - 新規企業（30日）: {overview['companies']['new_30d']}社")
            print(f"   - 新規企業（7日）: {overview['companies']['new_7d']}社")
            print(f"   - 支払い状況: 有効{overview['payments']['active']}件, トライアル{overview['payments']['trialing']}件")
            print(f"   - 解約数: {overview['cancellations']['total']}件")
            print(f"   - 通知数: {overview['notifications']['total']}件")
            print(f"   - アクティブコンテンツ: {overview['contents']['active']}件")
        else:
            print(f"❌ 概要統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 概要統計取得エラー: {e}")
    
    # 3. 解約統計取得
    print("\n3️⃣ 解約統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/cancellation", timeout=10)
        if response.status_code == 200:
            result = response.json()
            cancellation = result['cancellation_stats']
            print(f"✅ 解約統計取得成功:")
            print(f"   - 総解約数: {cancellation['total_cancellations']}件")
            print(f"   - 解約率: {cancellation['cancellation_rate']}%")
            print(f"   - 平均利用期間: {cancellation['avg_usage_days']}日")
            print(f"   - 解約理由別統計: {len(cancellation['reason_stats'])}件")
            print(f"   - 月別統計: {len(cancellation['monthly_stats'])}ヶ月")
        else:
            print(f"❌ 解約統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 解約統計取得エラー: {e}")
    
    # 4. 通知統計取得
    print("\n4️⃣ 通知統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/notification", timeout=10)
        if response.status_code == 200:
            result = response.json()
            notification = result['notification_stats']
            print(f"✅ 通知統計取得成功:")
            print(f"   - 総通知数: {notification['total_notifications']}件")
            print(f"   - 今日の通知: {notification['today_notifications']}件")
            print(f"   - 通知タイプ別: {len(notification['type_stats'])}種類")
            print(f"   - 企業別通知: {len(notification['company_notifications'])}社")
        else:
            print(f"❌ 通知統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 通知統計取得エラー: {e}")
    
    # 5. バックアップ統計取得
    print("\n5️⃣ バックアップ統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/backup", timeout=10)
        if response.status_code == 200:
            result = response.json()
            backup = result['backup_stats']
            print(f"✅ バックアップ統計取得成功:")
            print(f"   - 総バックアップ数: {backup['total_backups']}件")
            print(f"   - 総サイズ: {backup['total_size_mb']}MB")
            print(f"   - 企業別統計: {len(backup['company_stats'])}社")
            print(f"   - タイプ別統計: {len(backup['type_stats'])}種類")
        else:
            print(f"❌ バックアップ統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ バックアップ統計取得エラー: {e}")
    
    # 6. 収益分析取得
    print("\n6️⃣ 収益分析取得")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/revenue", timeout=10)
        if response.status_code == 200:
            result = response.json()
            revenue = result['revenue_analytics']
            print(f"✅ 収益分析取得成功:")
            print(f"   - 月別収益: {len(revenue['monthly_revenue'])}ヶ月")
            print(f"   - 業界別統計: {len(revenue['industry_stats'])}業界")
            print(f"   - 従業員数別統計: {len(revenue['employee_stats'])}区分")
            
            # 月別収益の詳細を表示
            if revenue['monthly_revenue']:
                latest_month = revenue['monthly_revenue'][-1]
                print(f"   - 最新月収益: {latest_month['month']} - ¥{latest_month['revenue']:,}")
        else:
            print(f"❌ 収益分析取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 収益分析取得エラー: {e}")
    
    # 7. 企業分析取得
    print("\n7️⃣ 企業分析取得")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/companies", timeout=10)
        if response.status_code == 200:
            result = response.json()
            companies = result['companies_analytics']
            print(f"✅ 企業分析取得成功: {len(companies)}社")
            
            # 上位3社の情報を表示
            for i, company in enumerate(companies[:3]):
                print(f"   {i+1}. {company['company_name']}: {company['subscription_status']} - コンテンツ{company['content_count']}件")
        else:
            print(f"❌ 企業分析取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 企業分析取得エラー: {e}")
    
    # 8. ダッシュボードサマリー取得
    print("\n8️⃣ ダッシュボードサマリー取得")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/summary", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ダッシュボードサマリー取得成功:")
            print(f"   - タイムスタンプ: {result['timestamp']}")
            print(f"   - 概要統計: {'取得済み' if result['overview'] else '未取得'}")
            print(f"   - 解約統計: {'取得済み' if result['cancellation'] else '未取得'}")
            print(f"   - 通知統計: {'取得済み' if result['notification'] else '未取得'}")
            print(f"   - バックアップ統計: {'取得済み' if result['backup'] else '未取得'}")
            print(f"   - 収益分析: {'取得済み' if result['revenue'] else '未取得'}")
        else:
            print(f"❌ ダッシュボードサマリー取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ダッシュボードサマリー取得エラー: {e}")
    
    # 9. リアルタイム統計取得
    print("\n9️⃣ リアルタイム統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/realtime", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ リアルタイム統計取得成功:")
            print(f"   - 現在時刻: {result['current_time']}")
            print(f"   - タイムスタンプ: {result['timestamp']}")
            
            if 'today' in result['stats']:
                today = result['stats']['today']
                print(f"   - 今日の通知: {today.get('notifications', 0)}件")
                print(f"   - 今日の新規企業: {today.get('new_companies', 0)}社")
        else:
            print(f"❌ リアルタイム統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ リアルタイム統計取得エラー: {e}")
    
    print("\n🎉 管理ダッシュボード機能統合テスト完了")
    return True

def test_dashboard_with_real_data():
    """実際のデータを使用したダッシュボードテスト"""
    print("\n=== 実際のデータを使用したダッシュボードテスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 既存の企業を取得して詳細分析をテスト
    try:
        response = requests.get(f"{base_url}/api/v1/companies", timeout=10)
        if response.status_code == 200:
            companies = response.json()['companies']
            if companies:
                test_company = companies[0]
                test_company_id = test_company['id']
                
                print(f"🔗 テスト対象企業: {test_company['company_name']} (ID: {test_company_id})")
                
                # 企業詳細分析を取得
                response = requests.get(f"{base_url}/api/v1/dashboard/companies/{test_company_id}/analytics", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    analytics = result['company_analytics']
                    
                    print(f"📊 企業詳細分析:")
                    print(f"   - 企業名: {analytics['company_info']['company_name']}")
                    print(f"   - 業界: {analytics['company_info']['industry']}")
                    print(f"   - 従業員数: {analytics['company_info']['employee_count']}人")
                    print(f"   - サブスクリプション状態: {analytics['subscription_info']['status']}")
                    print(f"   - コンテンツ数: {analytics['usage_stats']['content_count']}件")
                    print(f"   - 通知数: {analytics['usage_stats']['notification_count']}件")
                    
                    # コンテンツ履歴
                    if analytics['content_history']:
                        print(f"   - コンテンツ履歴: {len(analytics['content_history'])}件")
                        for content in analytics['content_history'][:3]:
                            print(f"     * {content['content_type']}: {content['created_at']}")
                    
                    # 通知履歴
                    if analytics['notification_history']:
                        print(f"   - 通知履歴: {len(analytics['notification_history'])}件")
                        for notification in analytics['notification_history'][:3]:
                            print(f"     * {notification['notification_type']}: {notification['sent_at']}")
                else:
                    print("❌ 企業詳細分析取得に失敗しました")
            else:
                print("❌ テスト可能な企業が見つかりません")
        else:
            print("❌ 企業一覧取得に失敗しました")
    except Exception as e:
        print(f"❌ 企業詳細分析テストエラー: {e}")

def test_dashboard_export():
    """ダッシュボードエクスポート機能のテスト"""
    print("\n=== ダッシュボードエクスポート機能テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # エクスポートタイプのリスト
    export_types = ['summary', 'overview', 'cancellation', 'notification', 'backup', 'revenue', 'companies']
    
    for export_type in export_types:
        try:
            print(f"📤 {export_type}エクスポートテスト")
            response = requests.get(f"{base_url}/api/v1/dashboard/export?type={export_type}", timeout=15)
            
            if response.status_code == 200:
                print(f"✅ {export_type}エクスポート成功")
                print(f"   - ファイルサイズ: {len(response.content)} bytes")
                
                # レスポンスヘッダーからファイル名を取得
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                    print(f"   - ファイル名: {filename}")
            else:
                print(f"❌ {export_type}エクスポート失敗: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {export_type}エクスポートエラー: {e}")

def test_dashboard_performance():
    """ダッシュボードパフォーマンステスト"""
    print("\n=== ダッシュボードパフォーマンステスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 各エンドポイントの応答時間を測定
    endpoints = [
        ('overview', '/api/v1/dashboard/overview'),
        ('cancellation', '/api/v1/dashboard/cancellation'),
        ('notification', '/api/v1/dashboard/notification'),
        ('backup', '/api/v1/dashboard/backup'),
        ('revenue', '/api/v1/dashboard/revenue'),
        ('companies', '/api/v1/dashboard/companies'),
        ('realtime', '/api/v1/dashboard/realtime')
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
    print("🚀 管理ダッシュボード機能テストを開始します")
    
    # 基本的な統合テスト
    if test_dashboard_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return
    
    # 実際のデータを使用したテスト
    test_dashboard_with_real_data()
    
    # エクスポート機能テスト
    test_dashboard_export()
    
    # パフォーマンステスト
    test_dashboard_performance()

if __name__ == "__main__":
    main() 