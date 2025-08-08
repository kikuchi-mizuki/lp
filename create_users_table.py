#!/usr/bin/env python3
"""
usersテーブルを作成するスクリプト
"""

import os
import psycopg2

def create_users_table():
    """usersテーブルを作成"""
    
    # 接続情報は環境変数から取得
    database_url = os.getenv('RAILWAY_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL/RAILWAY_DATABASE_URL is not set')
    
    try:
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        print(f'[SUCCESS] Railwayデータベース接続成功!')
        
        # usersテーブルを作成
        print("\n=== usersテーブルを作成中 ===")
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                line_user_id VARCHAR(255),
                stripe_customer_id VARCHAR(255),
                stripe_subscription_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # テーブルが作成されたか確認
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'users'
        """)
        
        result = c.fetchone()
        if result:
            print("✅ usersテーブルが正常に作成されました")
        else:
            print("❌ usersテーブルの作成に失敗しました")
        
        # テーブル構造を確認
        print("\n=== usersテーブルの構造 ===")
        c.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = c.fetchall()
        for col in columns:
            print(f"  カラム: {col[0]}, 型: {col[1]}, NULL許可: {col[2]}, デフォルト: {col[3]}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ usersテーブルの作成が完了しました")
        
    except Exception as e:
        print(f'[ERROR] usersテーブル作成エラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_users_table() 