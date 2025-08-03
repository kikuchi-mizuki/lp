#!/usr/bin/env python3
"""
企業関連テーブル作成スクリプト（SQLite用）
"""

from utils.db import get_db_connection

def create_company_tables():
    """企業関連のテーブルを作成（SQLite用）"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # companiesテーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                company_code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # company_line_accountsテーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_line_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                line_channel_id TEXT,
                line_access_token TEXT,
                line_channel_secret TEXT,
                webhook_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
            )
        ''')
        
        # company_deploymentsテーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                railway_project_id TEXT,
                railway_service_id TEXT,
                deployment_url TEXT,
                deployment_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        print("✅ 企業関連テーブルの作成が完了しました")
        
    except Exception as e:
        print(f"❌ テーブル作成エラー: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_company_tables() 