#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動スケジューラー統合テスト
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_scheduler_integration():
    """自動スケジューラー統合テスト"""
    print("=== 自動スケジューラー統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. スケジューラーAPI ヘルスチェック
    print("\n1️⃣ スケジューラーAPI ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/scheduler/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェック成功: {result['message']}")
            print(f"   - 実行状態: {'実行中' if result['is_running'] else '停止中'}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. スケジューラー状態取得
    print("\n2️⃣ スケジューラー状態取得")
    try:
        response = requests.get(f"{base_url}/api/v1/scheduler/status", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 状態取得成功:")
            print(f"   - 実行状態: {'実行中' if result['is_running'] else '停止中'}")
            print(f"   - 設定項目数: {len(result['schedule_config'])}件")
            for task_name, config in result['schedule_config'].items():
                status = "有効" if config['enabled'] else "無効"
                print(f"   - {task_name}: {status} ({config['time']})")
        else:
            print(f"❌ 状態取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 状態取得エラー: {e}")
    
    # 3. 利用可能なタスク一覧取得
    print("\n3️⃣ 利用可能なタスク一覧取得")
    try:
        response = requests.get(f"{base_url}/api/v1/scheduler/tasks", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ タスク一覧取得成功: {len(result['tasks'])}件")
            for task in result['tasks']:
                print(f"   - {task['name']}: {task['description']}")
                print(f"     スケジュール: {task['schedule']}")
        else:
            print(f"❌ タスク一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ タスク一覧取得エラー: {e}")
    
    # 4. スケジュール設定取得
    print("\n4️⃣ スケジュール設定取得")
    try:
        response = requests.get(f"{base_url}/api/v1/scheduler/config", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 設定取得成功: {len(result['schedule_config'])}件")
            for task_name, config in result['schedule_config'].items():
                status = "有効" if config['enabled'] else "無効"
                print(f"   - {task_name}: {status} ({config['time']})")
        else:
            print(f"❌ 設定取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 設定取得エラー: {e}")
    
    # 5. 手動タスク実行テスト
    print("\n5️⃣ 手動タスク実行テスト")
    test_tasks = ['notification_cleanup']  # 安全なタスクのみテスト
    
    for task_name in test_tasks:
        try:
            print(f"   🔄 タスク実行: {task_name}")
            response = requests.post(
                f"{base_url}/api/v1/scheduler/tasks/{task_name}/run",
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ タスク実行成功: {result['message']}")
            else:
                result = response.json()
                print(f"   ⚠️ タスク実行結果: {result.get('error', '不明なエラー')}")
        except Exception as e:
            print(f"   ❌ タスク実行エラー: {e}")
    
    # 6. 一括タスク実行テスト
    print("\n6️⃣ 一括タスク実行テスト")
    try:
        bulk_data = {
            'task_names': ['notification_cleanup']
        }
        response = requests.post(
            f"{base_url}/api/v1/scheduler/tasks/bulk-run",
            json=bulk_data,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 一括タスク実行成功:")
            for task_name, task_result in result['results'].items():
                status = "✅" if task_result['success'] else "❌"
                print(f"   - {task_name}: {status}")
        else:
            result = response.json()
            print(f"⚠️ 一括タスク実行結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 一括タスク実行エラー: {e}")
    
    # 7. スケジューラー開始テスト
    print("\n7️⃣ スケジューラー開始テスト")
    try:
        response = requests.post(f"{base_url}/api/v1/scheduler/start", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ スケジューラー開始成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ スケジューラー開始結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ スケジューラー開始エラー: {e}")
    
    # 8. スケジューラー停止テスト
    print("\n8️⃣ スケジューラー停止テスト")
    try:
        response = requests.post(f"{base_url}/api/v1/scheduler/stop", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ スケジューラー停止成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ スケジューラー停止結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ スケジューラー停止エラー: {e}")
    
    print("\n🎉 自動スケジューラー統合テスト完了")
    return True

def test_scheduler_with_real_data():
    """実際のデータを使用したスケジューラーテスト"""
    print("\n=== 実際のデータを使用したスケジューラーテスト ===")
    
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
                
                # 解約履歴を確認
                response = requests.get(f"{base_url}/api/v1/cancellation/history", timeout=10)
                if response.status_code == 200:
                    history = response.json()
                    print(f"📊 解約履歴: {history['count']}件")
                    
                    # 削除予定を確認
                    response = requests.get(f"{base_url}/api/v1/cancellation/pending-deletions", timeout=10)
                    if response.status_code == 200:
                        pending = response.json()
                        print(f"🗑️ 削除予定: {len(pending['pending_deletions'])}件")
                        
                        if pending['pending_deletions']:
                            print("✅ 削除予定があるため、削除チェックタスクをテストします")
                            test_deletion_check_task()
                        else:
                            print("⚠️ 削除予定がないため、削除チェックタスクはスキップします")
                    else:
                        print("❌ 削除予定確認に失敗しました")
                else:
                    print("❌ 解約履歴確認に失敗しました")
            else:
                print("❌ テスト可能な企業が見つかりません")
        else:
            print("❌ 企業一覧取得に失敗しました")
    except Exception as e:
        print(f"❌ 企業取得エラー: {e}")

def test_deletion_check_task():
    """削除チェックタスクのテスト"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        print("   🔄 削除チェックタスクを実行中...")
        response = requests.post(
            f"{base_url}/api/v1/scheduler/tasks/data_deletion_check/run",
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 削除チェックタスク実行成功: {result['message']}")
        else:
            result = response.json()
            print(f"   ⚠️ 削除チェックタスク実行結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"   ❌ 削除チェックタスク実行エラー: {e}")

def test_reminder_tasks():
    """リマインダータスクのテスト"""
    base_url = "http://127.0.0.1:5000"
    
    reminder_tasks = [
        'trial_ending_reminder',
        'renewal_reminder',
        'deletion_reminder'
    ]
    
    for task_name in reminder_tasks:
        try:
            print(f"   🔄 リマインダータスク実行: {task_name}")
            response = requests.post(
                f"{base_url}/api/v1/scheduler/tasks/{task_name}/run",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ リマインダータスク実行成功: {result['message']}")
            else:
                result = response.json()
                print(f"   ⚠️ リマインダータスク実行結果: {result.get('error', '不明なエラー')}")
        except Exception as e:
            print(f"   ❌ リマインダータスク実行エラー: {e}")

def main():
    """メイン関数"""
    print("🚀 自動スケジューラーテストを開始します")
    
    # 基本的な統合テスト
    if test_scheduler_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return
    
    # 実際のデータを使用したテスト
    test_scheduler_with_real_data()
    
    # リマインダータスクのテスト
    print("\n=== リマインダータスクテスト ===")
    test_reminder_tasks()

if __name__ == "__main__":
    main() 