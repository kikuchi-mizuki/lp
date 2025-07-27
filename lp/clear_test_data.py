#!/usr/bin/env python3
"""
テストデータクリア
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def clear_test_data():
    """テストデータをクリア"""
    print("=== テストデータクリア ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 使用量ログを削除
        c.execute('DELETE FROM usage_logs WHERE user_id = 1')
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ 削除完了: {deleted_count}件の使用量ログを削除しました")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    clear_test_data() 