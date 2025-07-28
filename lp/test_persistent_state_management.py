#!/usr/bin/env python3
"""
永続的な状態管理のテスト
"""

import os
from dotenv import load_dotenv
from models.user_state import get_user_state, set_user_state, clear_user_state, init_user_states_table

# 環境変数を読み込み
load_dotenv()

def test_persistent_state_management():
    """永続的な状態管理のテスト"""
    print("=== 永続的な状態管理のテスト ===")
    
    # テスト用のユーザーID
    test_user_id = "test_user_123"
    
    print("\n=== テスト内容 ===")
    print("1. user_statesテーブルの初期化")
    print("2. 状態の設定と取得")
    print("3. 状態の更新")
    print("4. 状態のクリア")
    
    try:
        # 1. テーブル初期化
        print("\n1. user_statesテーブルの初期化...")
        init_user_states_table()
        print("✅ テーブル初期化完了")
        
        # 2. 初期状態の確認
        print("\n2. 初期状態の確認...")
        initial_state = get_user_state(test_user_id)
        print(f"初期状態: {initial_state}")
        
        # 3. 状態の設定
        print("\n3. 状態をadd_selectに設定...")
        set_user_state(test_user_id, 'add_select')
        current_state = get_user_state(test_user_id)
        print(f"設定後の状態: {current_state}")
        
        # 4. 状態の更新
        print("\n4. 状態をconfirm_1に更新...")
        set_user_state(test_user_id, 'confirm_1')
        updated_state = get_user_state(test_user_id)
        print(f"更新後の状態: {updated_state}")
        
        # 5. 状態のクリア
        print("\n5. 状態をクリア...")
        clear_user_state(test_user_id)
        cleared_state = get_user_state(test_user_id)
        print(f"クリア後の状態: {cleared_state}")
        
        print("\n✅ 永続的な状態管理のテストが完了しました")
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")

if __name__ == "__main__":
    test_persistent_state_management() 