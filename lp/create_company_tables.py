#!/usr/bin/env python3
"""
企業関連テーブル作成スクリプト
"""

from utils.db import get_db_connection

def create_company_tables():
    """企業関連のテーブルを作成"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # companiesテーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                company_code VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # company_line_accountsテーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_line_accounts (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                line_channel_id VARCHAR(255),
                line_access_token TEXT,
                line_channel_secret VARCHAR(255),
                webhook_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
            )
        ''')
        
        # company_deploymentsテーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_deployments (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                railway_project_id VARCHAR(255),
                railway_service_id VARCHAR(255),
                deployment_url TEXT,
                deployment_status VARCHAR(50) DEFAULT 'pending',
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