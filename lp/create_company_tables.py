#!/usr/bin/env python3
"""
企業管理システム用データベーステーブル作成スクリプト
"""

import os
import sys
from utils.db import get_db_connection, get_db_type

def create_company_tables():
    """企業管理システム用のテーブルを作成"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        print("=== 企業管理システム用テーブル作成 ===")
        
        # データベースタイプを確認
        db_type = get_db_type()
        print(f"データベースタイプ: {db_type}")
        
        if db_type == 'postgresql':
            # PostgreSQL用のテーブル作成
            
            # 1. 企業基本情報テーブル
            print("📋 companiesテーブルを作成中...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(255) NOT NULL,
                    company_code VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    phone VARCHAR(50),
                    address TEXT,
                    industry VARCHAR(100),
                    employee_count INTEGER,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. 企業LINEアカウントテーブル
            print("📋 company_line_accountsテーブルを作成中...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_line_accounts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    line_channel_id VARCHAR(255) UNIQUE NOT NULL,
                    line_channel_access_token VARCHAR(255) NOT NULL,
                    line_channel_secret VARCHAR(255) NOT NULL,
                    line_basic_id VARCHAR(255),
                    line_qr_code_url VARCHAR(500),
                    webhook_url VARCHAR(500),
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            ''')
            
            # 3. 企業決済情報テーブル
            print("📋 company_paymentsテーブルを作成中...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_payments (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
                    stripe_subscription_id VARCHAR(255),
                    subscription_status VARCHAR(50),
                    current_period_start TIMESTAMP,
                    current_period_end TIMESTAMP,
                    trial_start TIMESTAMP,
                    trial_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            ''')
            
            # 4. 企業コンテンツ管理テーブル
            print("📋 company_contentsテーブルを作成中...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_contents (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    content_name VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    line_bot_url VARCHAR(500),
                    api_endpoint VARCHAR(500),
                    usage_count INTEGER DEFAULT 0,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            ''')
            
            # 5. 企業通知設定テーブル
            print("📋 company_notificationsテーブルを作成中...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_notifications (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    notification_type VARCHAR(100) NOT NULL,
                    is_enabled BOOLEAN DEFAULT TRUE,
                    recipients JSONB,
                    schedule VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            ''')
            
            # 6. 企業解約履歴テーブル
            print("📋 company_cancellationsテーブルを作成中...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_cancellations (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    cancellation_reason VARCHAR(255),
                    cancelled_by VARCHAR(100),
                    data_deletion_status VARCHAR(50) DEFAULT 'pending',
                    line_account_status VARCHAR(50) DEFAULT 'active',
                    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            ''')
            
            # 7. 企業ユーザー管理テーブル
            print("📋 company_usersテーブルを作成中...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_users (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role VARCHAR(50) DEFAULT 'user',
                    permissions JSONB,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(company_id, user_id)
                )
            ''')
            
        else:
            # SQLite用のテーブル作成（開発環境用）
            print("📋 SQLite用のテーブルを作成中...")
            
            # 1. 企業基本情報テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    company_code TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    address TEXT,
                    industry TEXT,
                    employee_count INTEGER,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. 企業LINEアカウントテーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_line_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    line_channel_id TEXT UNIQUE NOT NULL,
                    line_channel_access_token TEXT NOT NULL,
                    line_channel_secret TEXT NOT NULL,
                    line_basic_id TEXT,
                    line_qr_code_url TEXT,
                    webhook_url TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 3. 企業決済情報テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    stripe_customer_id TEXT UNIQUE NOT NULL,
                    stripe_subscription_id TEXT,
                    subscription_status TEXT,
                    current_period_start TIMESTAMP,
                    current_period_end TIMESTAMP,
                    trial_start TIMESTAMP,
                    trial_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 4. 企業コンテンツ管理テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    content_name TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    line_bot_url TEXT,
                    api_endpoint TEXT,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 5. 企業通知設定テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL,
                    is_enabled BOOLEAN DEFAULT 1,
                    recipients TEXT,
                    schedule TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 6. 企業解約履歴テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_cancellations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    cancellation_reason TEXT,
                    cancelled_by TEXT,
                    data_deletion_status TEXT DEFAULT 'pending',
                    line_account_status TEXT DEFAULT 'active',
                    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 7. 企業ユーザー管理テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'user',
                    permissions TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(company_id, user_id)
                )
            ''')
        
        conn.commit()
        print("✅ 企業管理システム用テーブル作成完了")
        
        # テーブル一覧を確認
        if db_type == 'postgresql':
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'company%'
                ORDER BY table_name
            """)
        else:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'company%'")
        
        tables = c.fetchall()
        print(f"\n📋 作成された企業管理テーブル:")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_company_tables()
    if success:
        print("\n🎉 企業管理システム用テーブルの作成が完了しました！")
    else:
        print("\n❌ テーブル作成に失敗しました。")
        sys.exit(1) 