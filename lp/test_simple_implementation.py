#!/usr/bin/env python3
"""
シンプルな実装テスト
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def test_simple_implementation():
    """シンプルな実装をテスト"""
    print("=== シンプルな実装テスト ===")
    
    # データベースに直接コンテンツを追加
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # テストユーザーID
        user_id = 2
        
        # 1個目のコンテンツを追加（無料）
        c.execute('''
            INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type, pending_charge)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, 1, None, True, "AI予定秘書", False))
        
        # 2個目のコンテンツを追加（¥1,500）
        c.execute('''
            INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type, pending_charge)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, 1, None, False, "AI経理秘書", True))
        
        # 3個目のコンテンツを追加（¥1,500）
        c.execute('''
            INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type, pending_charge)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, 1, None, False, "AIタスクコンシェルジュ", True))
        
        conn.commit()
        conn.close()
        
        print("✅ コンテンツ追加完了")
        
        # 結果確認
        print("\n=== 結果確認 ===")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, content_type, is_free, pending_charge, created_at
            FROM usage_logs
            WHERE user_id = %s
            ORDER BY created_at ASC
        ''', (user_id,))
        logs = c.fetchall()
        conn.close()
        
        print(f"使用量ログ総数: {len(logs)}件")
        
        for i, log in enumerate(logs, 1):
            log_id, content_type, is_free, pending_charge, created_at = log
            print(f"ログ{i}: {content_type}")
            print(f"  無料: {is_free}")
            print(f"  課金予定: {pending_charge}")
            print(f"  作成日時: {created_at}")
            print("---")
        
        # 課金構造の確認
        print("\n=== 課金構造確認 ===")
        free_count = sum(1 for log in logs if log[2])  # is_free
        paid_count = len(logs) - free_count
        
        print(f"📋 課金構造:")
        print(f"・AIコレクションズ → 月額3,900円")
        if paid_count > 0:
            print(f"・AIコレクションズ（追加） → ¥1,500/個 × {paid_count}個 = ¥{paid_count * 1500:,}円")
            print(f"・月額合計: ¥3,900 + ¥{paid_count * 1500:,} = ¥{3900 + paid_count * 1500:,}円")
        else:
            print(f"・AIコレクションズ（追加） → なし")
            print(f"・月額合計: ¥3,900円")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    test_simple_implementation() 