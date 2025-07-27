#!/usr/bin/env python3
"""
新しいコンテンツ追加テスト
"""

import os
from dotenv import load_dotenv
from services.line_service import handle_content_confirmation
from services.user_service import get_user_by_line_id

# 環境変数を読み込み
load_dotenv()

def test_new_content_addition():
    """新しいコンテンツ追加をテスト"""
    print("=== 新しいコンテンツ追加テスト ===")
    
    # テスト用のLINEユーザーID
    test_line_user_id = "U1234567890abcdef"
    
    # ユーザー情報を取得
    user = get_user_by_line_id(test_line_user_id)
    if not user:
        print("❌ テストユーザーが見つかりません")
        return
    
    print(f"✅ ユーザー取得成功: {user['id']}")
    print(f"Stripe Subscription ID: {user['stripe_subscription_id']}")
    
    # 新しいコンテンツを追加（4個目のコンテンツとして）
    print("\n=== 新しいコンテンツ追加シミュレート ===")
    
    # 既存のコンテンツを確認
    from utils.db import get_db_connection
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT content_type, COUNT(*) as count
        FROM usage_logs
        WHERE user_id = %s
        GROUP BY content_type
        ORDER BY content_type
    ''', (user['id'],))
    existing_content = c.fetchall()
    conn.close()
    
    print("既存のコンテンツ:")
    for content_type, count in existing_content:
        print(f"  {content_type}: {count}件")
    
    # 新しいコンテンツを追加（既存のコンテンツと異なるものを選択）
    content_options = ["AI予定秘書", "AI経理秘書", "AIタスクコンシェルジュ"]
    existing_types = [content[0] for content in existing_content]
    
    # 既存のコンテンツを除外して新しいコンテンツを選択
    available_content = [content for content in content_options if content not in existing_types]
    
    if not available_content:
        print("❌ 追加可能なコンテンツがありません")
        return
    
    # 新しいコンテンツを追加
    new_content_name = available_content[0]
    content_number_map = {
        "AI予定秘書": 1,
        "AI経理秘書": 2,
        "AIタスクコンシェルジュ": 3
    }
    
    content_number = content_number_map[new_content_name]
    
    print(f"\n新しいコンテンツを追加: {new_content_name} (content_number={content_number})")
    
    # コンテンツ追加を実行
    result = handle_content_confirmation(
        None,  # reply_token（テスト用）
        user['id'],
        user['stripe_subscription_id'],
        content_number,
        True  # confirmed
    )
    
    print(f"\n=== 実行結果 ===")
    print(f"結果: {result}")
    
    # 更新後のデータベース確認
    print("\n=== 更新後のデータベース確認 ===")
    try:
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
    test_new_content_addition() 