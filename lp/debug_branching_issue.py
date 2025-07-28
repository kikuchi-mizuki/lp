#!/usr/bin/env python3
"""
分岐問題の詳細デバッグ
"""

import os
from dotenv import load_dotenv
from models.user_state import get_user_state, set_user_state, clear_user_state
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def debug_branching_issue():
    """分岐問題の詳細デバッグ"""
    print("=== 分岐問題の詳細デバッグ ===")
    
    # テスト用のユーザーID
    test_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
    
    print(f"\n=== 現在の状態確認 ===")
    print(f"テストユーザーID: {test_user_id}")
    
    try:
        # 1. 現在の状態を確認
        current_state = get_user_state(test_user_id)
        print(f"現在の状態: {current_state}")
        
        # 2. add_select状態に設定
        print(f"\n=== add_select状態のテスト ===")
        set_user_state(test_user_id, 'add_select')
        new_state = get_user_state(test_user_id)
        print(f"設定後の状態: {new_state}")
        
        # 3. データベースで直接確認
        print(f"\n=== データベース直接確認 ===")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT line_user_id, state, updated_at FROM user_states WHERE line_user_id = %s', (test_user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            print(f"DB確認結果: line_user_id={result[0]}, state={result[1]}, updated_at={result[2]}")
        else:
            print("DB確認結果: レコードが見つかりません")
        
        # 4. 全ユーザー状態を確認
        print(f"\n=== 全ユーザー状態確認 ===")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT line_user_id, state, updated_at FROM user_states ORDER BY updated_at DESC LIMIT 5')
        results = c.fetchall()
        conn.close()
        
        for row in results:
            print(f"ユーザー: {row[0]}, 状態: {row[1]}, 更新: {row[2]}")
        
    except Exception as e:
        print(f"❌ デバッグエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_branching_issue() 