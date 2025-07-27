#!/usr/bin/env python3
"""
新しい実装のテスト
"""

import os
from dotenv import load_dotenv
from services.line_service import handle_content_confirmation
from services.user_service import get_user_by_line_id

# 環境変数を読み込み
load_dotenv()

def test_fresh_implementation():
    """新しい実装をテスト"""
    print("=== 新しい実装のテスト ===")
    
    # テスト用のLINEユーザーID
    test_line_user_id = "U1234567890abcdef"
    
    # ユーザー情報を取得
    user = get_user_by_line_id(test_line_user_id)
    if not user:
        print("❌ テストユーザーが見つかりません")
        return
    
    print(f"✅ ユーザー取得成功: {user['id']}")
    print(f"Stripe Subscription ID: {user['stripe_subscription_id']}")
    
    # 1個目のコンテンツを追加（無料）
    print("\n=== 1個目のコンテンツ追加テスト ===")
    
    result1 = handle_content_confirmation(
        None,  # reply_token（テスト用）
        user['id'],
        user['stripe_subscription_id'],
        1,  # AI予定秘書
        True  # confirmed
    )
    
    print(f"1個目追加結果: {result1}")
    
    # 2個目のコンテンツを追加（¥1,500）
    print("\n=== 2個目のコンテンツ追加テスト ===")
    
    result2 = handle_content_confirmation(
        None,  # reply_token（テスト用）
        user['id'],
        user['stripe_subscription_id'],
        2,  # AI経理秘書
        True  # confirmed
    )
    
    print(f"2個目追加結果: {result2}")
    
    # 3個目のコンテンツを追加（¥1,500）
    print("\n=== 3個目のコンテンツ追加テスト ===")
    
    result3 = handle_content_confirmation(
        None,  # reply_token（テスト用）
        user['id'],
        user['stripe_subscription_id'],
        3,  # AIタスクコンシェルジュ
        True  # confirmed
    )
    
    print(f"3個目追加結果: {result3}")
    
    # 最終確認
    print("\n=== 最終確認 ===")
    from utils.db import get_db_connection
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, content_type, is_free, pending_charge, created_at
        FROM usage_logs
        WHERE user_id = %s
        ORDER BY created_at ASC
    ''', (user['id'],))
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

if __name__ == "__main__":
    test_fresh_implementation() 