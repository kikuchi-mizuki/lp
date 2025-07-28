#!/usr/bin/env python3
"""
データベースタイプ確認スクリプト
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection, get_db_type

# 環境変数を読み込み
load_dotenv()

def check_database_type():
    """データベースタイプを確認"""
    print("=== データベースタイプ確認 ===")
    
    # 環境変数の確認
    database_url = os.getenv('DATABASE_URL')
    print(f"DATABASE_URL: {database_url}")
    
    # データベースタイプの確認
    db_type = get_db_type()
    print(f"データベースタイプ: {db_type}")
    
    # 実際の接続テスト
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # PostgreSQLの場合
        if db_type == 'postgresql':
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"PostgreSQLバージョン: {version[0]}")
            
            # user_statesテーブルの確認
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'user_states'
            """)
            table_exists = cursor.fetchone()
            print(f"user_statesテーブル存在: {table_exists is not None}")
            
        # SQLiteの場合
        else:
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()
            print(f"SQLiteバージョン: {version[0]}")
            
            # user_statesテーブルの確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_states'")
            table_exists = cursor.fetchone()
            print(f"user_statesテーブル存在: {table_exists is not None}")
        
        conn.close()
        print(f"✅ {db_type}で正常に接続できました")
        
    except Exception as e:
        print(f"❌ 接続エラー: {e}")

if __name__ == "__main__":
    check_database_type() 