#!/usr/bin/env python3
"""
データベーススキーマ修正スクリプト
"""

import os
import psycopg2
from utils.db import get_db_connection

def fix_database_schema():
    """データベーススキーマを修正"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        print("データベーススキーマ修正開始...")
        
        # user_statesテーブルの修正
        print("user_statesテーブルを修正中...")
        
        # 既存のテーブルを削除
        c.execute("DROP TABLE IF EXISTS user_states")
        
        # 新しいスキーマでテーブルを作成
        c.execute('''
            CREATE TABLE user_states (
                id SERIAL PRIMARY KEY,
                line_user_id VARCHAR(255) UNIQUE,
                state VARCHAR(100) DEFAULT 'initial',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # companiesテーブルの修正
        print("companiesテーブルを修正中...")
        
        # line_user_idカラムが存在しない場合は追加
        c.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'companies' AND column_name = 'line_user_id'
                ) THEN
                    ALTER TABLE companies ADD COLUMN line_user_id VARCHAR(255);
                END IF;
            END $$;
        """)
        
        # テストデータを作成
        print("テストデータを作成中...")
        
        # 企業データ
        c.execute('''
            INSERT INTO companies (company_name, line_user_id, stripe_subscription_id, subscription_status, current_period_start, current_period_end, trial_end, company_code) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (line_user_id) DO UPDATE SET
                stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                subscription_status = EXCLUDED.subscription_status,
                current_period_start = EXCLUDED.current_period_start,
                current_period_end = EXCLUDED.current_period_end,
                trial_end = EXCLUDED.trial_end
        ''', (
            'サンプル株式会社',
            'U1b9d0d75b0c770dc1107dde349d572f7',
            'sub_1RuM84Ixg6C5hAVdp1EIGCrm',
            'trialing',
            '2025-01-10 00:00:00',
            '2025-02-10 00:00:00',
            '2025-02-10 00:00:00',
            'SAMPLE001'
        ))
        
        # ユーザー状態データ
        c.execute('''
            INSERT INTO user_states (line_user_id, state) 
            VALUES (%s, %s)
            ON CONFLICT (line_user_id) DO UPDATE SET
                state = EXCLUDED.state,
                updated_at = CURRENT_TIMESTAMP
        ''', ('U1b9d0d75b0c770dc1107dde349d572f7', 'welcome_sent'))
        
        conn.commit()
        print("データベーススキーマ修正完了")
        
        # 確認クエリ
        c.execute("SELECT * FROM user_states")
        user_states = c.fetchall()
        print(f"user_statesテーブル: {len(user_states)}件")
        
        c.execute("SELECT * FROM companies")
        companies = c.fetchall()
        print(f"companiesテーブル: {len(companies)}件")
        
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database_schema()
