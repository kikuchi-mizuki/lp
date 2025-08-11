#!/usr/bin/env python3
"""
スプレッドシートの更新内容を反映するスクリプト
"""

import os
import sys
import json
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def update_spreadsheet_content():
    """スプレッドシートの内容を強制更新"""
    try:
        from services.spreadsheet_content_service import SpreadsheetContentService
        
        print("🔄 スプレッドシートの内容を更新中...")
        
        # サービスインスタンスを作成
        service = SpreadsheetContentService()
        
        # 強制更新を実行
        result = service.get_available_contents(force_refresh=True)
        
        if result['success']:
            print("✅ スプレッドシートの更新が完了しました")
            
            if result.get('fallback'):
                print("⚠️  フォールバック用のデフォルトコンテンツを使用しています")
                print("   理由: Google認証情報が設定されていないか、スプレッドシートにアクセスできません")
            
            # 取得されたコンテンツを表示
            contents = result['contents']
            print(f"\n📋 取得されたコンテンツ ({len(contents)}件):")
            for content_id, content_info in contents.items():
                print(f"  - {content_info.get('name', 'Unknown')} (ID: {content_id})")
                print(f"    説明: {content_info.get('description', 'No description')}")
                print(f"    価格: ¥{content_info.get('price', 0):,}")
                print(f"    ステータス: {content_info.get('status', 'unknown')}")
                print()
            
            return True
        else:
            print("❌ スプレッドシートの更新に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def check_environment_variables():
    """環境変数の設定状況を確認"""
    print("🔍 環境変数の設定状況を確認中...")
    
    required_vars = {
        'CONTENT_SPREADSHEET_ID': 'スプレッドシートID',
        'GOOGLE_CREDENTIALS_FILE': 'Google認証情報ファイル',
        'GOOGLE_CREDENTIALS_JSON': 'Google認証情報JSON'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {description}: 設定済み")
        else:
            print(f"  ❌ {description}: 未設定")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  以下の環境変数が設定されていません:")
        for var in missing_vars:
            print(f"    - {var}")
        print("\nこれらの変数をRailwayの環境変数で設定してください。")
    
    return len(missing_vars) == 0

def main():
    """メイン処理"""
    print("🚀 スプレッドシート更新スクリプトを開始します")
    print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 環境変数の確認
    env_ok = check_environment_variables()
    print()
    
    # スプレッドシートの更新
    success = update_spreadsheet_content()
    
    print()
    if success:
        print("🎉 処理が完了しました")
    else:
        print("💥 処理に失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()
