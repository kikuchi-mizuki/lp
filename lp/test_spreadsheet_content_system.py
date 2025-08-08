#!/usr/bin/env python3
"""
スプレッドシート連携コンテンツ管理システムのテスト
"""

import os
import sys
import requests
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.spreadsheet_content_service import spreadsheet_content_service

def test_spreadsheet_content_service():
    """スプレッドシート連携サービスのテスト"""
    print("🧪 スプレッドシート連携コンテンツ管理システムテスト")
    print("=" * 60)
    
    # 1. 基本機能テスト
    print("\n📋 1. 基本機能テスト")
    
    # 利用可能なコンテンツ取得
    print("  📊 利用可能なコンテンツ取得...")
    result = spreadsheet_content_service.get_available_contents()
    
    if result['success']:
        print(f"  ✅ 成功: {len(result['contents'])}件のコンテンツを取得")
        for content_id, content_info in result['contents'].items():
            print(f"     - {content_id}: {content_info['name']} ({content_info['price']}円)")
    else:
        print(f"  ❌ 失敗: {result.get('error', '不明なエラー')}")
    
    # 2. キャッシュ機能テスト
    print("\n📋 2. キャッシュ機能テスト")
    
    # キャッシュ付きで取得
    cached_result = spreadsheet_content_service.get_available_contents()
    print(f"  📊 キャッシュ状態: {cached_result.get('cached', False)}")
    
    # 強制更新
    print("  🔄 キャッシュ強制更新...")
    refresh_result = spreadsheet_content_service.refresh_cache()
    print(f"  📊 更新後キャッシュ状態: {refresh_result.get('cached', False)}")
    
    # 3. 特定コンテンツ取得テスト
    print("\n📋 3. 特定コンテンツ取得テスト")
    
    test_content_id = 'ai_accounting'
    content = spreadsheet_content_service.get_content_by_id(test_content_id)
    
    if content:
        print(f"  ✅ {test_content_id}取得成功:")
        print(f"     名前: {content['name']}")
        print(f"     説明: {content['description']}")
        print(f"     料金: {content['price']}円")
        print(f"     URL: {content['url']}")
    else:
        print(f"  ❌ {test_content_id}取得失敗")
    
    # 4. フォールバック機能テスト
    print("\n📋 4. フォールバック機能テスト")
    
    # スプレッドシートIDを一時的に無効にしてフォールバックをテスト
    original_id = spreadsheet_content_service.spreadsheet_id
    spreadsheet_content_service.spreadsheet_id = 'invalid_id'
    
    fallback_result = spreadsheet_content_service.get_available_contents(force_refresh=True)
    print(f"  📊 フォールバック状態: {fallback_result.get('fallback', False)}")
    
    if fallback_result.get('fallback'):
        print(f"  ✅ フォールバック機能正常: {len(fallback_result['contents'])}件のデフォルトコンテンツ")
    else:
        print("  ⚠️ フォールバック機能が動作していません")
    
    # 元に戻す
    spreadsheet_content_service.spreadsheet_id = original_id

def test_api_endpoints():
    """APIエンドポイントのテスト"""
    print("\n🌐 APIエンドポイントテスト")
    print("=" * 60)
    
    base_url = "http://localhost:5000"  # ローカルテスト用
    
    # 1. コンテンツ一覧取得API
    print("\n📋 1. コンテンツ一覧取得API")
    try:
        response = requests.get(f"{base_url}/api/v1/content/list")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功: {len(data.get('contents', {}))}件のコンテンツ")
        else:
            print(f"  ❌ 失敗: {response.status_code}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # 2. コンテンツ情報取得API
    print("\n📋 2. コンテンツ情報取得API")
    try:
        response = requests.get(f"{base_url}/api/v1/content/ai_accounting")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功: {data['content']['name']}")
        else:
            print(f"  ❌ 失敗: {response.status_code}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # 3. 健全性チェックAPI
    print("\n📋 3. 健全性チェックAPI")
    try:
        response = requests.get(f"{base_url}/api/v1/content/health")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功: スプレッドシート接続={data.get('spreadsheet_connection')}")
            print(f"     コンテンツ数: {data.get('contents_count')}")
            print(f"     キャッシュ状態: {data.get('cache_status')}")
            print(f"     フォールバックモード: {data.get('fallback_mode')}")
        else:
            print(f"  ❌ 失敗: {response.status_code}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")

def test_content_management():
    """コンテンツ管理機能のテスト"""
    print("\n🔧 コンテンツ管理機能テスト")
    print("=" * 60)
    
    # 新しいコンテンツの追加テスト（実際には追加しない）
    print("\n📋 1. 新規コンテンツ追加テスト（シミュレーション）")
    
    new_content = {
        'id': 'ai_marketing',
        'name': 'AIマーケティングアシスタント',
        'description': 'マーケティング戦略をAIが最適化',
        'url': 'https://example.com/marketing',
        'price': 3980,
        'features': ['SNS分析', '競合分析', 'キャンペーン最適化']
    }
    
    print(f"  📝 追加予定コンテンツ:")
    print(f"     ID: {new_content['id']}")
    print(f"     名前: {new_content['name']}")
    print(f"     料金: {new_content['price']}円")
    print(f"     機能: {', '.join(new_content['features'])}")
    
    # 2. ステータス更新テスト（シミュレーション）
    print("\n📋 2. ステータス更新テスト（シミュレーション）")
    
    test_statuses = ['active', 'inactive', 'maintenance']
    for status in test_statuses:
        print(f"  📊 ステータス「{status}」への更新シミュレーション")
    
    # 3. データベース同期テスト（シミュレーション）
    print("\n📋 3. データベース同期テスト（シミュレーション）")
    
    print("  🔄 スプレッドシート → データベース同期シミュレーション")
    print("     - 既存コンテンツの更新")
    print("     - 新規コンテンツの追加")
    print("     - 無効コンテンツの除外")

def main():
    """メイン実行関数"""
    print("🚀 スプレッドシート連携コンテンツ管理システムテスト開始")
    print("=" * 80)
    
    # 環境変数チェック
    print("\n🔍 環境変数チェック")
    required_env_vars = [
        'CONTENT_SPREADSHEET_ID',
        'GOOGLE_CREDENTIALS_FILE',
        'GOOGLE_CREDENTIALS_JSON'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"  ⚠️ 未設定の環境変数: {', '.join(missing_vars)}")
        print("  📝 env_example_spreadsheet.txtを参考に環境変数を設定してください")
    else:
        print("  ✅ 必要な環境変数が設定されています")
    
    # テスト実行
    try:
        test_spreadsheet_content_service()
        test_api_endpoints()
        test_content_management()
        
        print("\n🎉 テスト完了")
        print("=" * 80)
        print("📋 次のステップ:")
        print("  1. Google Sheets APIの設定")
        print("  2. スプレッドシートの作成と共有設定")
        print("  3. 環境変数の設定")
        print("  4. アプリケーションの再起動")
        print("  5. 実際のコンテンツ追加テスト")
        
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
