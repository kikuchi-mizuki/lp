#!/usr/bin/env python3
"""
登録ユーザー確認
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def check_users():
    """登録ユーザーを確認"""
    print("=== 登録ユーザー確認 ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # PostgreSQL用のテーブル情報取得
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        columns = c.fetchall()
        print(f"usersテーブルのカラム ({len(columns)}件):")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
        # ユーザー一覧を取得
        c.execute('SELECT * FROM users ORDER BY created_at DESC')
        users = c.fetchall()
        conn.close()
        
        print(f"\n登録ユーザー数: {len(users)}")
        for i, user in enumerate(users, 1):
            print(f"ユーザー{i}: {user}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_users() 