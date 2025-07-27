#!/usr/bin/env python3
"""
使用量ログ詳細確認
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def check_usage_logs_detailed():
    """使用量ログの詳細を確認"""
    print("=== 使用量ログ詳細確認 ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 全使用量ログを取得
        c.execute('''
            SELECT id, user_id, usage_quantity, stripe_usage_record_id, 
                   is_free, content_type, pending_charge, created_at 
            FROM usage_logs 
            ORDER BY created_at DESC
        ''')
        logs = c.fetchall()
        conn.close()
        
        print(f"使用量ログ総数: {len(logs)}件")
        print("\n=== 詳細一覧 ===")
        
        for i, log in enumerate(logs, 1):
            log_id, user_id, usage_quantity, stripe_usage_record_id, is_free, content_type, pending_charge, created_at = log
            print(f"ログ{i}:")
            print(f"  ID: {log_id}")
            print(f"  ユーザーID: {user_id}")
            print(f"  使用量: {usage_quantity}")
            print(f"  Stripe Usage Record ID: {stripe_usage_record_id}")
            print(f"  無料: {is_free}")
            print(f"  コンテンツ: {content_type}")
            print(f"  課金予定: {pending_charge}")
            print(f"  作成日時: {created_at}")
            print("---")
            
        # 統計情報
        print("\n=== 統計情報 ===")
        
        # 無料コンテンツ数
        free_count = sum(1 for log in logs if log[4])  # is_free
        paid_count = len(logs) - free_count
        
        print(f"無料コンテンツ: {free_count}件")
        print(f"有料コンテンツ: {paid_count}件")
        
        # コンテンツ別集計
        content_types = {}
        for log in logs:
            content_type = log[5]  # content_type
            if content_type not in content_types:
                content_types[content_type] = 0
            content_types[content_type] += 1
        
        print(f"\nコンテンツ別集計:")
        for content_type, count in content_types.items():
            print(f"  {content_type}: {count}件")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_usage_logs_detailed() 