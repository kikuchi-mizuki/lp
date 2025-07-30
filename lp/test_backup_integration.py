#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
データバックアップ機能統合テスト
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta

def test_backup_integration():
    """データバックアップ機能統合テスト"""
    print("=== データバックアップ機能統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. バックアップAPI ヘルスチェック
    print("\n1️⃣ バックアップAPI ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/backup/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェック成功: {result['message']}")
            print(f"   - バックアップディレクトリ: {'存在' if result['backup_directory_exists'] else '不存在'}")
            print(f"   - バックアップファイル数: {result['backup_count']}件")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. バックアップ統計取得
    print("\n2️⃣ バックアップ統計取得")
    try:
        response = requests.get(f"{base_url}/api/v1/backup/statistics", timeout=10)
        if response.status_code == 200:
            result = response.json()
            stats = result['statistics']
            print(f"✅ バックアップ統計取得成功:")
            print(f"   - 総バックアップ数: {stats['total_backups']}件")
            print(f"   - 総サイズ: {stats['total_size_mb']}MB")
            print(f"   - 企業別統計: {len(stats['company_stats'])}件")
            print(f"   - タイプ別統計: {len(stats['type_stats'])}件")
        else:
            print(f"❌ バックアップ統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ バックアップ統計取得エラー: {e}")
    
    # 3. 全バックアップ一覧取得
    print("\n3️⃣ 全バックアップ一覧取得")
    try:
        response = requests.get(f"{base_url}/api/v1/backup/list", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ バックアップ一覧取得成功: {result['count']}件")
            for backup in result['backups'][:3]:  # 最新3件を表示
                print(f"   - {backup['filename']}: {backup['file_size_mb']}MB")
        else:
            print(f"❌ バックアップ一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ バックアップ一覧取得エラー: {e}")
    
    # 4. 企業別バックアップ一覧取得
    print("\n4️⃣ 企業別バックアップ一覧取得")
    try:
        test_company_id = 1
        response = requests.get(f"{base_url}/api/v1/backup/companies/{test_company_id}/list", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 企業別バックアップ一覧取得成功: {result['count']}件")
            for backup in result['backups']:
                print(f"   - {backup['filename']}: {backup['file_size_mb']}MB")
        else:
            print(f"❌ 企業別バックアップ一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 企業別バックアップ一覧取得エラー: {e}")
    
    # 5. バックアップ作成テスト
    print("\n5️⃣ バックアップ作成テスト")
    try:
        test_company_id = 1
        backup_data = {
            'backup_type': 'full'
        }
        response = requests.post(
            f"{base_url}/api/v1/backup/companies/{test_company_id}/create",
            json=backup_data,
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ バックアップ作成成功: {result['message']}")
            print(f"   - ファイル名: {result['backup_file']}")
            print(f"   - ファイルサイズ: {result['backup_size']} bytes")
            print(f"   - データ数: {result['data_count']}件")
            
            # 作成されたバックアップファイル名を保存
            created_backup_file = result['backup_file']
        else:
            result = response.json()
            print(f"⚠️ バックアップ作成結果: {result.get('error', '不明なエラー')}")
            created_backup_file = None
    except Exception as e:
        print(f"❌ バックアップ作成エラー: {e}")
        created_backup_file = None
    
    # 6. バックアッププレビューテスト
    if created_backup_file:
        print("\n6️⃣ バックアッププレビューテスト")
        try:
            response = requests.get(
                f"{base_url}/api/v1/backup/companies/{test_company_id}/preview/{created_backup_file}",
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ バックアッププレビュー成功: {result['message']}")
                data_summary = result['data_summary']
                print(f"   - 企業情報: 1件")
                print(f"   - LINEアカウント: {data_summary['line_accounts']}件")
                print(f"   - 支払い情報: {data_summary['payments']}件")
                print(f"   - コンテンツ: {data_summary['contents']}件")
                print(f"   - 通知履歴: {data_summary['notifications']}件")
                print(f"   - 解約履歴: {data_summary['cancellations']}件")
            else:
                result = response.json()
                print(f"⚠️ バックアッププレビュー結果: {result.get('error', '不明なエラー')}")
        except Exception as e:
            print(f"❌ バックアッププレビューエラー: {e}")
    
    # 7. 一括バックアップ作成テスト
    print("\n7️⃣ 一括バックアップ作成テスト")
    try:
        test_company_id = 1
        bulk_data = {
            'backup_types': ['full']
        }
        response = requests.post(
            f"{base_url}/api/v1/backup/companies/{test_company_id}/bulk-create",
            json=bulk_data,
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 一括バックアップ作成成功:")
            for backup_type, backup_result in result['results'].items():
                status = "✅" if backup_result['success'] else "❌"
                print(f"   - {backup_type}: {status}")
        else:
            result = response.json()
            print(f"⚠️ 一括バックアップ作成結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 一括バックアップ作成エラー: {e}")
    
    # 8. バックアップダウンロードテスト
    if created_backup_file:
        print("\n8️⃣ バックアップダウンロードテスト")
        try:
            response = requests.get(
                f"{base_url}/api/v1/backup/download/{created_backup_file}",
                timeout=30
            )
            if response.status_code == 200:
                print(f"✅ バックアップダウンロード成功")
                print(f"   - ファイルサイズ: {len(response.content)} bytes")
                
                # ダウンロードしたファイルを保存
                download_path = f"test_download_{created_backup_file}"
                with open(download_path, 'wb') as f:
                    f.write(response.content)
                print(f"   - 保存先: {download_path}")
            else:
                result = response.json()
                print(f"⚠️ バックアップダウンロード結果: {result.get('error', '不明なエラー')}")
        except Exception as e:
            print(f"❌ バックアップダウンロードエラー: {e}")
    
    # 9. 古いバックアップクリーンアップテスト
    print("\n9️⃣ 古いバックアップクリーンアップテスト")
    try:
        cleanup_data = {
            'days_to_keep': 30
        }
        response = requests.post(
            f"{base_url}/api/v1/backup/cleanup",
            json=cleanup_data,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ バックアップクリーンアップ成功: {result['message']}")
            print(f"   - 削除件数: {result['deleted_count']}件")
        else:
            result = response.json()
            print(f"⚠️ バックアップクリーンアップ結果: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ バックアップクリーンアップエラー: {e}")
    
    print("\n🎉 データバックアップ機能統合テスト完了")
    return True

def test_backup_with_real_data():
    """実際のデータを使用したバックアップテスト"""
    print("\n=== 実際のデータを使用したバックアップテスト ===")
    
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
                
                # 企業の詳細情報を確認
                response = requests.get(f"{base_url}/api/v1/companies/{test_company_id}", timeout=10)
                if response.status_code == 200:
                    company_detail = response.json()
                    print(f"📊 企業詳細:")
                    print(f"   - 企業名: {company_detail['company']['company_name']}")
                    print(f"   - 業界: {company_detail['company'].get('industry', '未設定')}")
                    print(f"   - 従業員数: {company_detail['company'].get('employee_count', 0)}人")
                    
                    # バックアップを作成
                    print("✅ 企業データのバックアップを作成します")
                    test_company_backup(test_company_id)
                else:
                    print("❌ 企業詳細取得に失敗しました")
            else:
                print("❌ テスト可能な企業が見つかりません")
        else:
            print("❌ 企業一覧取得に失敗しました")
    except Exception as e:
        print(f"❌ 企業取得エラー: {e}")

def test_company_backup(company_id):
    """企業バックアップのテスト"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        # バックアップを作成
        backup_data = {
            'backup_type': 'full'
        }
        response = requests.post(
            f"{base_url}/api/v1/backup/companies/{company_id}/create",
            json=backup_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ バックアップ作成成功: {result['message']}")
            print(f"   - ファイル名: {result['backup_file']}")
            print(f"   - ファイルサイズ: {result['backup_size']} bytes")
            
            # バックアップの内容をプレビュー
            backup_file = result['backup_file']
            preview_response = requests.get(
                f"{base_url}/api/v1/backup/companies/{company_id}/preview/{backup_file}",
                timeout=30
            )
            
            if preview_response.status_code == 200:
                preview_result = preview_response.json()
                data_summary = preview_result['data_summary']
                print(f"📋 バックアップ内容:")
                print(f"   - LINEアカウント: {data_summary['line_accounts']}件")
                print(f"   - 支払い情報: {data_summary['payments']}件")
                print(f"   - コンテンツ: {data_summary['contents']}件")
                print(f"   - 通知履歴: {data_summary['notifications']}件")
                print(f"   - 解約履歴: {data_summary['cancellations']}件")
                print(f"   - サブスクリプション期間: {data_summary['subscription_periods']}件")
                print(f"   - 使用ログ: {data_summary['usage_logs']}件")
            else:
                print("❌ バックアッププレビューに失敗しました")
        else:
            result = response.json()
            print(f"❌ バックアップ作成失敗: {result.get('error', '不明なエラー')}")
    except Exception as e:
        print(f"❌ 企業バックアップテストエラー: {e}")

def test_backup_restore():
    """バックアップ復元のテスト"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        # バックアップ一覧を取得
        response = requests.get(f"{base_url}/api/v1/backup/list", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result['backups']:
                # 最新のバックアップを使用
                latest_backup = result['backups'][0]
                backup_file_path = latest_backup['file_path']
                company_id = latest_backup['company_id']
                
                print(f"🔄 バックアップ復元テスト: {latest_backup['filename']}")
                
                # 復元プレビュー
                restore_data = {
                    'backup_file_path': backup_file_path,
                    'restore_mode': 'preview'
                }
                response = requests.post(
                    f"{base_url}/api/v1/backup/companies/{company_id}/restore",
                    json=restore_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 復元プレビュー成功: {result['message']}")
                    data_summary = result['data_summary']
                    print(f"📋 復元予定データ:")
                    for key, value in data_summary.items():
                        print(f"   - {key}: {value}件")
                else:
                    result = response.json()
                    print(f"❌ 復元プレビュー失敗: {result.get('error', '不明なエラー')}")
            else:
                print("⚠️ 復元テスト用のバックアップファイルが見つかりません")
        else:
            print("❌ バックアップ一覧取得に失敗しました")
    except Exception as e:
        print(f"❌ バックアップ復元テストエラー: {e}")

def main():
    """メイン関数"""
    print("🚀 データバックアップ機能テストを開始します")
    
    # 基本的な統合テスト
    if test_backup_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return
    
    # 実際のデータを使用したテスト
    test_backup_with_real_data()
    
    # バックアップ復元テスト
    print("\n=== バックアップ復元テスト ===")
    test_backup_restore()

if __name__ == "__main__":
    main() 