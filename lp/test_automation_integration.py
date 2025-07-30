#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動化機能統合テスト
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_automation_integration():
    """自動化機能統合テスト"""
    print("=== 自動化機能統合テスト ===")

    base_url = "http://127.0.0.1:5000"

    print(f"🌐 ベースURL: {base_url}")

    # 1. 自動化API ヘルスチェック
    print("\n1️⃣ 自動化API ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/automation/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェック成功: {result['message']}")
            print(f"   - サービス状態: {result['status']}")
            print(f"   - 実行状態: {result['is_running']}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False

    # 2. 自動化状態取得
    print("\n2️⃣ 自動化状態取得")
    try:
        response = requests.get(f"{base_url}/api/v1/automation/status", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 状態取得成功")
            print(f"   - 実行中: {result['status']['is_running']}")
            print(f"   - 設定項目数: {len(result['status']['config'])}")
        else:
            print(f"❌ 状態取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 状態取得エラー: {e}")

    # 3. 利用可能タスク取得
    print("\n3️⃣ 利用可能タスク取得")
    try:
        response = requests.get(f"{base_url}/api/v1/automation/tasks", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ タスク取得成功")
            for task_name, task_info in result['tasks'].items():
                print(f"   - {task_info['name']}: {task_info['description']}")
        else:
            print(f"❌ タスク取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ タスク取得エラー: {e}")

    # 4. 自動化設定取得
    print("\n4️⃣ 自動化設定取得")
    try:
        response = requests.get(f"{base_url}/api/v1/automation/config", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 設定取得成功")
            for config_name, config_info in result['config'].items():
                print(f"   - {config_name}: 有効={config_info.get('enabled', False)}")
        else:
            print(f"❌ 設定取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 設定取得エラー: {e}")

    # 5. 手動バックアップ実行
    print("\n5️⃣ 手動バックアップ実行")
    try:
        response = requests.post(f"{base_url}/api/v1/automation/backup", 
                               json={'company_id': None}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ バックアップ実行成功: {result['message']}")
        else:
            print(f"❌ バックアップ実行失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ バックアップ実行エラー: {e}")

    # 6. 手動クリーンアップ実行
    print("\n6️⃣ 手動クリーンアップ実行")
    try:
        response = requests.post(f"{base_url}/api/v1/automation/cleanup", 
                               json={'type': 'logs'}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ クリーンアップ実行成功: {result['message']}")
        else:
            print(f"❌ クリーンアップ実行失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ クリーンアップ実行エラー: {e}")

    # 7. 手動データ同期実行
    print("\n7️⃣ 手動データ同期実行")
    try:
        response = requests.post(f"{base_url}/api/v1/automation/sync", 
                               json={'type': 'integrity'}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ データ同期実行成功: {result['message']}")
        else:
            print(f"❌ データ同期実行失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ データ同期実行エラー: {e}")

    # 8. 特定タスク実行
    print("\n8️⃣ 特定タスク実行")
    try:
        response = requests.post(f"{base_url}/api/v1/automation/tasks/health_check/run", 
                               timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェックタスク実行成功")
        else:
            print(f"❌ ヘルスチェックタスク実行失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ヘルスチェックタスク実行エラー: {e}")

    # 9. 自動化ログ取得
    print("\n9️⃣ 自動化ログ取得")
    try:
        response = requests.get(f"{base_url}/api/v1/automation/logs", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ログ取得成功: {len(result['logs'])}件")
            for log in result['logs'][:3]:  # 最新3件を表示
                print(f"   - {log['timestamp']}: {log['message']}")
        else:
            print(f"❌ ログ取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ログ取得エラー: {e}")

    # 10. 自動化統計取得
    print("\n🔟 自動化統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/automation/statistics", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 統計取得成功")
            stats = result['statistics']
            print(f"   - 総バックアップ数: {stats['total_backups']}")
            print(f"   - 成功率: {stats['success_rate']}%")
            print(f"   - 平均実行時間: {stats['average_execution_time']}秒")
        else:
            print(f"❌ 統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 統計取得エラー: {e}")

    print("\n🎉 自動化機能統合テスト完了")
    return True

def test_automation_with_real_data():
    """実際のデータを使用した自動化テスト"""
    print("\n=== 実際のデータを使用した自動化テスト ===")

    base_url = "http://127.0.0.1:5000"

    # 1. 企業データの取得
    print("\n1️⃣ 企業データの取得")
    try:
        response = requests.get(f"{base_url}/api/v1/companies", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result['success'] and result['companies']:
                company = result['companies'][0]
                company_id = company['id']
                print(f"✅ 企業データ取得成功: {company['name']} (ID: {company_id})")
                
                # 2. 特定企業のバックアップ実行
                print(f"\n2️⃣ 企業 {company['name']} のバックアップ実行")
                backup_response = requests.post(f"{base_url}/api/v1/automation/backup", 
                                              json={'company_id': company_id}, timeout=60)
                if backup_response.status_code == 200:
                    backup_result = backup_response.json()
                    print(f"✅ 企業バックアップ成功: {backup_result['message']}")
                else:
                    print(f"❌ 企業バックアップ失敗: {backup_response.status_code}")
            else:
                print("⚠️ テスト用の企業データが見つかりません")
        else:
            print(f"❌ 企業データ取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 企業データ取得エラー: {e}")

    # 3. 全体的な自動化テスト
    print("\n3️⃣ 全体的な自動化テスト")
    try:
        # バックアップ実行
        backup_response = requests.post(f"{base_url}/api/v1/automation/backup", 
                                      json={'company_id': None}, timeout=120)
        if backup_response.status_code == 200:
            print("✅ 全体バックアップ成功")
        else:
            print(f"❌ 全体バックアップ失敗: {backup_response.status_code}")

        # クリーンアップ実行
        cleanup_response = requests.post(f"{base_url}/api/v1/automation/cleanup", 
                                       json={'type': 'all'}, timeout=60)
        if cleanup_response.status_code == 200:
            print("✅ 全体クリーンアップ成功")
        else:
            print(f"❌ 全体クリーンアップ失敗: {cleanup_response.status_code}")

        # データ同期実行
        sync_response = requests.post(f"{base_url}/api/v1/automation/sync", 
                                    json={'type': 'all'}, timeout=60)
        if sync_response.status_code == 200:
            print("✅ 全体データ同期成功")
        else:
            print(f"❌ 全体データ同期失敗: {sync_response.status_code}")

    except Exception as e:
        print(f"❌ 全体的な自動化テストエラー: {e}")

def test_automation_performance():
    """自動化機能のパフォーマンステスト"""
    print("\n=== 自動化機能パフォーマンステスト ===")

    base_url = "http://127.0.0.1:5000"

    # 1. ヘルスチェックの応答時間測定
    print("\n1️⃣ ヘルスチェック応答時間測定")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/v1/automation/health", timeout=10)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # ミリ秒
        
        if response.status_code == 200:
            print(f"✅ ヘルスチェック成功: {response_time:.2f}ms")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code} ({response_time:.2f}ms)")
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")

    # 2. 状態取得の応答時間測定
    print("\n2️⃣ 状態取得応答時間測定")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/v1/automation/status", timeout=10)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # ミリ秒
        
        if response.status_code == 200:
            print(f"✅ 状態取得成功: {response_time:.2f}ms")
        else:
            print(f"❌ 状態取得失敗: {response.status_code} ({response_time:.2f}ms)")
    except Exception as e:
        print(f"❌ 状態取得エラー: {e}")

    # 3. タスク実行の応答時間測定
    print("\n3️⃣ タスク実行応答時間測定")
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/api/v1/automation/tasks/health_check/run", timeout=30)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # ミリ秒
        
        if response.status_code == 200:
            print(f"✅ タスク実行成功: {response_time:.2f}ms")
        else:
            print(f"❌ タスク実行失敗: {response.status_code} ({response_time:.2f}ms)")
    except Exception as e:
        print(f"❌ タスク実行エラー: {e}")

    # 4. 並行リクエストテスト
    print("\n4️⃣ 並行リクエストテスト")
    try:
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get(f"{base_url}/api/v1/automation/health", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        # 10個の並行リクエスト
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        print(f"✅ 並行リクエスト結果: {success_count}/10 成功")
        
    except Exception as e:
        print(f"❌ 並行リクエストテストエラー: {e}")

def main():
    """メイン関数"""
    print("🚀 自動化機能テストを開始します")

    # 基本的な統合テスト
    if test_automation_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return

    # 実際のデータを使用したテスト
    test_automation_with_real_data()

    # パフォーマンステスト
    test_automation_performance()

    print("\n🎉 すべての自動化機能テストが完了しました")

if __name__ == "__main__":
    main() 