#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解約処理・データ削除システム統合テスト
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_cancellation_integration():
    """解約処理統合テスト"""
    print("=== 解約処理・データ削除システム統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # テスト企業ID（既存の企業を使用）
    test_company_id = 1
    
    print(f"🔗 テスト対象企業ID: {test_company_id}")
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. 解約・データ削除API ヘルスチェック
    print("\n1️⃣ 解約・データ削除API ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/cancellation/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェック成功: {result['message']}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. 解約理由一覧取得
    print("\n2️⃣ 解約理由一覧取得")
    try:
        response = requests.get(f"{base_url}/api/v1/cancellation/reasons", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 解約理由取得成功: {len(result['reasons'])}件")
            for reason_code, reason_text in result['reasons'].items():
                print(f"   - {reason_code}: {reason_text}")
        else:
            print(f"❌ 解約理由取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 解約理由取得エラー: {e}")
    
    # 3. 企業の解約状況確認
    print("\n3️⃣ 企業の解約状況確認")
    try:
        response = requests.get(f"{base_url}/api/v1/cancellation/companies/{test_company_id}/cancellation-status", timeout=10)
        if response.status_code == 200:
            result = response.json()
            status = result['status']
            print(f"✅ 解約状況確認成功:")
            print(f"   - 企業名: {status['company_name']}")
            print(f"   - ステータス: {status['company_status']}")
            print(f"   - 解約済み: {status['is_cancelled']}")
        else:
            print(f"❌ 解約状況確認失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 解約状況確認エラー: {e}")
    
    # 4. 解約履歴取得
    print("\n4️⃣ 解約履歴取得")
    try:
        response = requests.get(f"{base_url}/api/v1/cancellation/history", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 解約履歴取得成功: {result['count']}件")
            for cancellation in result['cancellations'][:3]:  # 最新3件を表示
                print(f"   - {cancellation['company_name']}: {cancellation['cancelled_at']}")
        else:
            print(f"❌ 解約履歴取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 解約履歴取得エラー: {e}")
    
    # 5. 削除予定企業取得
    print("\n5️⃣ 削除予定企業取得")
    try:
        response = requests.get(f"{base_url}/api/v1/cancellation/pending-deletions", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 削除予定企業取得成功: {result['count']}件")
            for pending in result['pending_deletions'][:3]:  # 最新3件を表示
                print(f"   - {pending['company_name']}: {pending['scheduled_deletion_date']}")
        else:
            print(f"❌ 削除予定企業取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 削除予定企業取得エラー: {e}")
    
    # 6. 企業解約処理（テスト用）
    print("\n6️⃣ 企業解約処理（テスト用）")
    try:
        cancellation_data = {
            'reason': 'not_used',
            'notes': 'テスト用解約処理'
        }
        response = requests.post(
            f"{base_url}/api/v1/cancellation/companies/{test_company_id}/cancel",
            json=cancellation_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 解約処理成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ 解約処理結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 解約処理エラー: {e}")
    
    # 7. 削除スケジュール設定（テスト用）
    print("\n7️⃣ 削除スケジュール設定（テスト用）")
    try:
        schedule_data = {
            'deletion_days': 7  # 7日後に削除
        }
        response = requests.post(
            f"{base_url}/api/v1/cancellation/companies/{test_company_id}/schedule-deletion",
            json=schedule_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 削除スケジュール設定成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ 削除スケジュール設定結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 削除スケジュール設定エラー: {e}")
    
    # 8. 削除スケジュールキャンセル（テスト用）
    print("\n8️⃣ 削除スケジュールキャンセル（テスト用）")
    try:
        response = requests.post(
            f"{base_url}/api/v1/cancellation/companies/{test_company_id}/cancel-deletion-schedule",
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 削除スケジュールキャンセル成功: {result['message']}")
        else:
            result = response.json()
            print(f"⚠️ 削除スケジュールキャンセル結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 削除スケジュールキャンセルエラー: {e}")
    
    print("\n🎉 解約処理・データ削除システム統合テスト完了")
    return True

def test_cancellation_with_real_data():
    """実際のデータを使用した解約処理テスト"""
    print("\n=== 実際のデータを使用した解約処理テスト ===")
    
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
                
                # 解約状況を確認
                response = requests.get(f"{base_url}/api/v1/cancellation/companies/{test_company_id}/cancellation-status", timeout=10)
                if response.status_code == 200:
                    status = response.json()['status']
                    print(f"📊 現在の状況:")
                    print(f"   - ステータス: {status['company_status']}")
                    print(f"   - 解約済み: {status['is_cancelled']}")
                    
                    if not status['is_cancelled']:
                        print("✅ テスト可能な企業です")
                        return test_company_id
                    else:
                        print("⚠️ 既に解約済みの企業です")
                else:
                    print("❌ 解約状況確認に失敗しました")
            else:
                print("❌ テスト可能な企業が見つかりません")
        else:
            print("❌ 企業一覧取得に失敗しました")
    except Exception as e:
        print(f"❌ 企業取得エラー: {e}")
    
    return None

def main():
    """メイン関数"""
    print("🚀 解約処理・データ削除システムテストを開始します")
    
    # 基本的な統合テスト
    if test_cancellation_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return
    
    # 実際のデータを使用したテスト
    test_company_id = test_cancellation_with_real_data()
    if test_company_id:
        print(f"✅ 実際のデータテスト準備完了: 企業ID {test_company_id}")
    else:
        print("⚠️ 実際のデータテストはスキップします")

if __name__ == "__main__":
    main() 