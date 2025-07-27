#!/usr/bin/env python3
"""
分岐処理のデバッグテスト
"""

import os
from dotenv import load_dotenv
from services.line_service import handle_add_content, handle_content_selection, handle_content_confirmation
from services.user_service import get_user_by_line_id

# 環境変数を読み込み
load_dotenv()

def test_branching_debug():
    """分岐処理のデバッグテスト"""
    print("=== 分岐処理のデバッグテスト ===")
    
    # テスト用のLINEユーザーID
    test_line_user_id = "U1234567890abcdef"
    
    # ユーザー情報を取得
    user = get_user_by_line_id(test_line_user_id)
    if not user:
        print("❌ テストユーザーが見つかりません")
        return
    
    print(f"✅ ユーザー取得成功: {user['id']}")
    print(f"Stripe Subscription ID: {user['stripe_subscription_id']}")
    
    # 1. コンテンツ追加メニューのテスト
    print("\n=== 1. コンテンツ追加メニューのテスト ===")
    try:
        result = handle_add_content(
            None,  # reply_token（テスト用）
            user['id'],
            user['stripe_subscription_id']
        )
        print(f"✅ handle_add_content実行成功")
    except Exception as e:
        print(f"❌ handle_add_content実行エラー: {e}")
    
    # 2. コンテンツ選択のテスト
    print("\n=== 2. コンテンツ選択のテスト ===")
    try:
        result = handle_content_selection(
            None,  # reply_token（テスト用）
            user['id'],
            user['stripe_subscription_id'],
            "1"  # AI予定秘書
        )
        print(f"✅ handle_content_selection実行成功")
    except Exception as e:
        print(f"❌ handle_content_selection実行エラー: {e}")
    
    # 3. コンテンツ確認のテスト
    print("\n=== 3. コンテンツ確認のテスト ===")
    try:
        result = handle_content_confirmation(
            None,  # reply_token（テスト用）
            user['id'],
            user['stripe_subscription_id'],
            "1",  # AI予定秘書
            True  # confirmed
        )
        print(f"✅ handle_content_confirmation実行成功")
    except Exception as e:
        print(f"❌ handle_content_confirmation実行エラー: {e}")
    
    # 4. データベース確認
    print("\n=== 4. データベース確認 ===")
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
    
    # 5. 分岐処理の分析
    print("\n=== 5. 分岐処理の分析 ===")
    print("✅ 期待される分岐フロー:")
    print("  1. ユーザーが「追加」を入力")
    print("  2. handle_add_content() → コンテンツ選択メニュー表示")
    print("  3. ユーザーが「1」を入力")
    print("  4. handle_content_selection() → コンテンツ確認メッセージ表示")
    print("  5. ユーザーが「はい」を入力")
    print("  6. handle_content_confirmation() → コンテンツ追加完了")
    
    print("\n❌ 現在の問題:")
    print("  - ユーザーが「1」を入力した後にウェルカムメッセージが表示される")
    print("  - 分岐処理が正しく動作していない可能性")

if __name__ == "__main__":
    test_branching_debug() 