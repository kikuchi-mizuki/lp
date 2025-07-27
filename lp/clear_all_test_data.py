#!/usr/bin/env python3
"""
すべてのテストデータクリア
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def clear_all_test_data():
    """すべてのテストデータをクリア"""
    print("=== すべてのテストデータクリア ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 使用量ログを削除
        c.execute('DELETE FROM usage_logs')
        usage_deleted = c.rowcount
        
        # ユーザーを削除
        c.execute('DELETE FROM users')
        users_deleted = c.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ 削除完了:")
        print(f"  - 使用量ログ: {usage_deleted}件削除")
        print(f"  - ユーザー: {users_deleted}件削除")
        print(f"  - データベースがクリアされました")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    clear_all_test_data() 