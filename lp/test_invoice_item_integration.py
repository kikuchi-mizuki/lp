#!/usr/bin/env python3
"""
Invoice Item統合テスト
"""

import os
from dotenv import load_dotenv
from services.line_service import handle_content_confirmation
from services.user_service import get_user_by_line_id

# 環境変数を読み込み
load_dotenv()

def test_invoice_item_integration():
    """Invoice Item統合をテスト"""
    print("=== Invoice Item統合テスト ===")
    
    # テスト用のLINEユーザーID
    test_line_user_id = "U1234567890abcdef"
    
    # ユーザー情報を取得
    user = get_user_by_line_id(test_line_user_id)
    if not user:
        print("❌ テストユーザーが見つかりません")
        return
    
    print(f"✅ ユーザー取得成功: {user['id']}")
    print(f"Stripe Subscription ID: {user['stripe_subscription_id']}")
    
    # コンテンツ追加をシミュレート（2個目以降で課金対象）
    print("\n=== コンテンツ追加シミュレート（Invoice Item統合） ===")
    
    # 新しいコンテンツを追加（4個目のコンテンツ）
    result = handle_content_confirmation(
        None,  # reply_token（テスト用）
        user['id'],
        user['stripe_subscription_id'],
        3,  # AIタスクコンシェルジュ
        True  # confirmed
    )
    
    print(f"\n=== 実行結果 ===")
    print(f"結果: {result}")
    
    # データベース確認
    print("\n=== データベース確認 ===")
    try:
        from utils.db import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, user_id, usage_quantity, stripe_usage_record_id,
                   is_free, content_type, pending_charge, created_at
            FROM usage_logs
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        ''', (user['id'],))
        logs = c.fetchall()
        conn.close()
        
        print(f"最新の使用量ログ ({len(logs)}件):")
        for log in logs:
            print(f"  ID: {log[0]}, 数量: {log[2]}, Stripe ID: {log[3]}, 無料: {log[4]}, コンテンツ: {log[5]}, 課金予定: {log[6]}, 作成日時: {log[7]}")
            
    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")

if __name__ == "__main__":
    test_invoice_item_integration() 