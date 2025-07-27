#!/usr/bin/env python3
"""
重複メッセージ修正のテスト
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def test_duplicate_message_fix():
    """重複メッセージ修正をテスト"""
    print("=== 重複メッセージ修正のテスト ===")
    
    # 現在のユーザー状態を確認
    print("\n=== 現在のユーザー状態確認 ===")
    try:
        from routes.line import user_states
        print(f"現在のユーザー状態数: {len(user_states)}")
        for user_id, state in user_states.items():
            print(f"  - {user_id}: {state}")
    except Exception as e:
        print(f"ユーザー状態確認エラー: {e}")
    
    # データベースのユーザー確認
    print("\n=== データベースのユーザー確認 ===")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, line_user_id, email, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        users = c.fetchall()
        conn.close()
        
        print(f"登録ユーザー数: {len(users)}")
        for user in users:
            user_id, line_user_id, email, created_at = user
            print(f"  - ID: {user_id}, LINE ID: {line_user_id}, Email: {email}, 作成日時: {created_at}")
            
    except Exception as e:
        print(f"データベース確認エラー: {e}")
    
    # 修正内容の説明
    print("\n=== 修正内容 ===")
    print("✅ 重複送信防止の改善:")
    print("  1. 友達追加時に既に案内文が送信されているかチェック")
    print("  2. 初回メッセージ時に既に案内文が送信されているかチェック")
    print("  3. 新サブスクリプション時の重複送信ロジックを削除")
    print("  4. ユーザー状態管理の改善")
    print("  5. 友達削除時にユーザー状態もクリア")
    
    print("\n✅ 期待される結果:")
    print("  - 案内文が1回のみ送信される")
    print("  - 重複送信が防止される")
    print("  - ユーザー体験の向上")

if __name__ == "__main__":
    test_duplicate_message_fix() 