#!/usr/bin/env python3
"""
情報引き継ぎの流れテスト
"""

import os
from dotenv import load_dotenv
from models.user_state import get_user_state, set_user_state, clear_user_state
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def test_information_flow():
    """情報引き継ぎの流れテスト"""
    print("=== 情報引き継ぎの流れテスト ===")
    
    # テスト用のユーザーID
    test_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
    
    print(f"\n=== 情報引き継ぎの流れ確認 ===")
    print("1. 初期状態: welcome_sent")
    print("2. 「追加」コマンド: add_select")
    print("3. 「1」入力: confirm_1")
    print("4. 「はい」入力: welcome_sent")
    
    try:
        # 1. 初期状態の確認
        print(f"\n1. 初期状態の確認")
        clear_user_state(test_user_id)
        initial_state = get_user_state(test_user_id)
        print(f"初期状態: {initial_state}")
        
        # 2. 「追加」コマンドのシミュレーション
        print(f"\n2. 「追加」コマンドのシミュレーション")
        set_user_state(test_user_id, 'add_select')
        add_state = get_user_state(test_user_id)
        print(f"add_select状態: {add_state}")
        
        # 3. 「1」入力のシミュレーション
        print(f"\n3. 「1」入力のシミュレーション")
        set_user_state(test_user_id, 'confirm_1')
        confirm_state = get_user_state(test_user_id)
        print(f"confirm_1状態: {confirm_state}")
        
        # 4. 状態からコンテンツ番号を抽出
        print(f"\n4. 状態からコンテンツ番号を抽出")
        content_number = confirm_state.split('_')[1]
        print(f"抽出されたコンテンツ番号: {content_number}")
        
        # 5. 「はい」入力のシミュレーション
        print(f"\n5. 「はい」入力のシミュレーション")
        set_user_state(test_user_id, 'welcome_sent')
        final_state = get_user_state(test_user_id)
        print(f"最終状態: {final_state}")
        
        # 6. データベースでの確認
        print(f"\n6. データベースでの確認")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT line_user_id, state, updated_at FROM user_states WHERE line_user_id = %s', (test_user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            print(f"DB確認結果: line_user_id={result[0]}, state={result[1]}, updated_at={result[2]}")
        else:
            print("DB確認結果: レコードが見つかりません")
        
        print(f"\n✅ 情報引き継ぎの流れテストが完了しました")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_information_flow() 