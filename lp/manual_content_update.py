#!/usr/bin/env python3
"""
手動でコンテンツを更新するスクリプト
スプレッドシートが利用できない場合の代替手段
"""

import os
import sys
import json
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def update_content_manually():
    """手動でコンテンツ情報を更新"""
    
    # 新しいコンテンツ情報（ここにスプレッドシートの更新内容を反映）
    updated_contents = {
        'ai_accounting': {
            'name': 'AI経理秘書',
            'description': '経理作業をAIが効率化',
            'url': 'https://lp-production-9e2c.up.railway.app/accounting',
            'price': 1500,
            'status': 'active',
            'created_at': '2024-01-01',
            'features': ['自動仕訳', '帳簿作成', '税務申告', '経営分析']
        },
        'ai_schedule': {
            'name': 'AI予定秘書',
            'description': 'スケジュール管理をAIがサポート',
            'url': 'https://lp-production-9e2c.up.railway.app/schedule',
            'price': 1500,
            'status': 'active',
            'created_at': '2024-01-01',
            'features': ['スケジュール管理', '会議調整', 'リマインダー', 'タスク管理']
        },
        'ai_task': {
            'name': 'AIタスクコンシェルジュ',
            'description': 'タスク管理をAIが最適化',
            'url': 'https://lp-production-9e2c.up.railway.app/task',
            'price': 1500,
            'status': 'active',
            'created_at': '2024-01-01',
            'features': ['タスク管理', 'プロジェクト管理', '進捗追跡', 'チーム連携']
        }
    }
    
    # ここにスプレッドシートの更新内容を追加
    # 例：
    # updated_contents['new_service'] = {
    #     'name': '新しいサービス名',
    #     'description': '新しいサービスの説明',
    #     'url': 'https://example.com',
    #     'price': 2000,
    #     'status': 'active',
    #     'created_at': datetime.now().strftime('%Y-%m-%d'),
    #     'features': ['新機能1', '新機能2']
    # }
    
    try:
        from services.spreadsheet_content_service import SpreadsheetContentService
        
        print("🔄 手動でコンテンツを更新中...")
        
        # サービスインスタンスを作成
        service = SpreadsheetContentService()
        
        # キャッシュを手動で更新
        service.cached_contents = updated_contents
        service.last_cache_update = datetime.now().timestamp()
        
        print("✅ コンテンツの手動更新が完了しました")
        
        # 更新されたコンテンツを表示
        print(f"\n📋 更新されたコンテンツ ({len(updated_contents)}件):")
        for content_id, content_info in updated_contents.items():
            print(f"  - {content_info.get('name', 'Unknown')} (ID: {content_id})")
            print(f"    説明: {content_info.get('description', 'No description')}")
            print(f"    価格: ¥{content_info.get('price', 0):,}")
            print(f"    ステータス: {content_info.get('status', 'unknown')}")
            print(f"    機能: {', '.join(content_info.get('features', []))}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 手動コンテンツ更新スクリプトを開始します")
    print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("📝 このスクリプトを使用してスプレッドシートの更新内容を手動で反映できます。")
    print("   スプレッドシートの内容を確認し、上記の updated_contents 辞書を更新してください。")
    print()
    
    # コンテンツの更新
    success = update_content_manually()
    
    print()
    if success:
        print("🎉 処理が完了しました")
        print("💡 アプリケーションを再起動すると、更新されたコンテンツが反映されます。")
    else:
        print("💥 処理に失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()
