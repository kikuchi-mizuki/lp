#!/usr/bin/env python3
import os
import sys
from utils.db import get_db_connection, get_db_type

def create_missing_tables():
    """不足しているテーブルを作成"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        print("=== 不足テーブル作成 ===")
        
        # subscription_periodsテーブルの作成
        print("📋 subscription_periodsテーブルを作成中...")
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscription_periods (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                stripe_subscription_id VARCHAR(255),
                subscription_status VARCHAR(50),
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # cancellation_historyテーブルの作成
        print("📋 cancellation_historyテーブルを作成中...")
        c.execute('''
            CREATE TABLE IF NOT EXISTS cancellation_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                restriction_start TIMESTAMP,
                restriction_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ テーブル作成完了")
        
        # テーブル一覧を確認
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = c.fetchall()
        print(f"\n📋 現在のテーブル一覧:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_missing_tables() 