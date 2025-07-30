#!/usr/bin/env python3
"""
Railway PostgreSQL用企業管理テーブル作成スクリプト
"""

import os
import psycopg2
import sys

def create_company_tables_railway():
    """RailwayのPostgreSQLに企業管理テーブルを作成"""
    print("=== Railway PostgreSQL用企業管理テーブル作成 ===")
    
    # 環境変数からDATABASE_URLを取得
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL環境変数が設定されていません")
        print("💡 RailwayのデータベースURLを設定してください")
        return False
    
    if not database_url.startswith('postgresql://'):
        print("❌ DATABASE_URLがPostgreSQL接続URLではありません")
        print(f"現在のURL: {database_url}")
        return False
    
    try:
        # RailwayのPostgreSQLに接続
        print(f"🔗 Railway PostgreSQLに接続中...")
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 接続情報を表示
        c.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
        db_info = c.fetchone()
        print(f"✅ 接続成功")
        print(f"  データベース: {db_info[0]}")
        print(f"  ユーザー: {db_info[1]}")
        print(f"  サーバー: {db_info[2]}:{db_info[3]}")
        
        # 既存のテーブルを確認
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        existing_tables = [table[0] for table in c.fetchall()]
        
        print(f"\n📋 既存テーブル ({len(existing_tables)}件):")
        for table in existing_tables:
            print(f"  - {table}")
        
        # 企業管理テーブル一覧
        company_tables = [
            'companies',
            'company_line_accounts',
            'company_payments',
            'company_contents',
            'company_notifications',
            'company_cancellations',
            'company_users'
        ]
        
        # 既に存在する企業管理テーブルを確認
        existing_company_tables = [table for table in existing_tables if table in company_tables]
        print(f"\n🏢 既存の企業管理テーブル ({len(existing_company_tables)}件):")
        for table in existing_company_tables:
            print(f"  - {table}")
        
        # 作成が必要なテーブルを確認
        tables_to_create = [table for table in company_tables if table not in existing_tables]
        print(f"\n📝 作成が必要なテーブル ({len(tables_to_create)}件):")
        for table in tables_to_create:
            print(f"  - {table}")
        
        if not tables_to_create:
            print(f"\n✅ すべての企業管理テーブルが既に存在します")
            return True
        
        # テーブル作成
        print(f"\n🚀 テーブル作成を開始...")
        
        # 1. 企業基本情報テーブル
        if 'companies' in tables_to_create:
            print(f"📋 companiesテーブルを作成中...")
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
        if 'company_line_accounts' in tables_to_create:
            print(f"📋 company_line_accountsテーブルを作成中...")
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
        if 'company_payments' in tables_to_create:
            print(f"📋 company_paymentsテーブルを作成中...")
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
        if 'company_contents' in tables_to_create:
            print(f"📋 company_contentsテーブルを作成中...")
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
        if 'company_notifications' in tables_to_create:
            print(f"📋 company_notificationsテーブルを作成中...")
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
        if 'company_cancellations' in tables_to_create:
            print(f"📋 company_cancellationsテーブルを作成中...")
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
        if 'company_users' in tables_to_create:
            print(f"📋 company_usersテーブルを作成中...")
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
        
        conn.commit()
        print(f"✅ 企業管理テーブル作成完了")
        
        # 作成後のテーブル一覧を確認
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'company%'
            ORDER BY table_name
        """)
        created_tables = c.fetchall()
        
        print(f"\n📋 作成された企業管理テーブル:")
        for table in created_tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Railway PostgreSQL用企業管理テーブル作成を開始します...")
    print("注意: DATABASE_URL環境変数が設定されていることを確認してください")
    print()
    
    success = create_company_tables_railway()
    if success:
        print(f"\n🎉 Railway PostgreSQL用企業管理テーブルの作成が完了しました！")
        print(f"💡 PostgreSQL管理画面で企業管理テーブルを確認してください")
    else:
        print(f"\n❌ テーブル作成に失敗しました。")
        sys.exit(1) 