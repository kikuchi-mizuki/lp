#!/usr/bin/env python3
"""
自動データベース検出・企業管理テーブル作成スクリプト
"""

import os
import psycopg2
import sqlite3
import sys
from urllib.parse import urlparse

def test_database_connection(connection_info):
    """データベース接続をテスト"""
    try:
        if connection_info['type'] == 'postgresql':
            conn = psycopg2.connect(
                host=connection_info['host'],
                database=connection_info['database'],
                user=connection_info['user'],
                password=connection_info['password'],
                port=connection_info['port']
            )
        else:
            conn = sqlite3.connect(connection_info['database'])
        
        conn.close()
        return True
    except Exception as e:
        return False

def get_available_databases():
    """利用可能なデータベース接続を検出"""
    databases = []
    
    # 1. 環境変数DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        try:
            parsed = urlparse(database_url)
            if parsed.scheme == 'postgresql':
                databases.append({
                    'name': '環境変数DATABASE_URL',
                    'type': 'postgresql',
                    'host': parsed.hostname,
                    'port': parsed.port or 5432,
                    'database': parsed.path[1:],
                    'user': parsed.username,
                    'password': parsed.password,
                    'url': database_url
                })
        except Exception as e:
            print(f"⚠️ DATABASE_URL解析エラー: {e}")
    
    # 2. ローカルPostgreSQL接続
    local_postgres_configs = [
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'ai_collections',
            'user': 'postgres',
            'password': 'password'
        },
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'password'
        },
        {
            'host': '127.0.0.1',
            'port': 5432,
            'database': 'ai_collections',
            'user': 'postgres',
            'password': 'password'
        }
    ]
    
    for i, config in enumerate(local_postgres_configs):
        if test_database_connection({'type': 'postgresql', **config}):
            databases.append({
                'name': f'ローカルPostgreSQL {i+1}',
                'type': 'postgresql',
                **config
            })
    
    # 3. SQLite
    sqlite_paths = ['database.db', '../database.db', '../../database.db']
    for path in sqlite_paths:
        if os.path.exists(path):
            databases.append({
                'name': f'SQLite ({path})',
                'type': 'sqlite',
                'database': path
            })
    
    return databases

def create_company_tables(database_info):
    """指定されたデータベースに企業管理テーブルを作成"""
    print(f"\n🚀 {database_info['name']}に企業管理テーブルを作成中...")
    
    try:
        if database_info['type'] == 'postgresql':
            conn = psycopg2.connect(
                host=database_info['host'],
                database=database_info['database'],
                user=database_info['user'],
                password=database_info['password'],
                port=database_info['port']
            )
        else:
            conn = sqlite3.connect(database_info['database'])
        
        c = conn.cursor()
        
        # 接続情報を表示
        if database_info['type'] == 'postgresql':
            c.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
            db_info = c.fetchone()
            print(f"✅ 接続成功")
            print(f"  データベース: {db_info[0]}")
            print(f"  ユーザー: {db_info[1]}")
            print(f"  サーバー: {db_info[2]}:{db_info[3]}")
        else:
            print(f"✅ SQLite接続成功")
            print(f"  データベース: {database_info['database']}")
        
        # 既存のテーブルを確認
        if database_info['type'] == 'postgresql':
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        else:
            c.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
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
        
        if database_info['type'] == 'postgresql':
            # PostgreSQL用のテーブル作成
            create_postgresql_tables(c, tables_to_create)
        else:
            # SQLite用のテーブル作成
            create_sqlite_tables(c, tables_to_create)
        
        conn.commit()
        print(f"✅ 企業管理テーブル作成完了")
        
        # 作成後のテーブル一覧を確認
        if database_info['type'] == 'postgresql':
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'company%'
                ORDER BY table_name
            """)
        else:
            c.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name LIKE 'company%'
                ORDER BY name
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

def create_postgresql_tables(cursor, tables_to_create):
    """PostgreSQL用テーブル作成"""
    
    # 1. 企業基本情報テーブル
    if 'companies' in tables_to_create:
        print(f"📋 companiesテーブルを作成中...")
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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

def create_sqlite_tables(cursor, tables_to_create):
    """SQLite用テーブル作成"""
    
    # 1. 企業基本情報テーブル
    if 'companies' in tables_to_create:
        print(f"📋 companiesテーブルを作成中...")
        cursor.execute('''
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
    if 'company_line_accounts' in tables_to_create:
        print(f"📋 company_line_accountsテーブルを作成中...")
        cursor.execute('''
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
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        ''')
    
    # 3. 企業決済情報テーブル
    if 'company_payments' in tables_to_create:
        print(f"📋 company_paymentsテーブルを作成中...")
        cursor.execute('''
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
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        ''')
    
    # 4. 企業コンテンツ管理テーブル
    if 'company_contents' in tables_to_create:
        print(f"📋 company_contentsテーブルを作成中...")
        cursor.execute('''
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
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        ''')
    
    # 5. 企業通知設定テーブル
    if 'company_notifications' in tables_to_create:
        print(f"📋 company_notificationsテーブルを作成中...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                is_enabled INTEGER DEFAULT 1,
                recipients TEXT,
                schedule TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        ''')
    
    # 6. 企業解約履歴テーブル
    if 'company_cancellations' in tables_to_create:
        print(f"📋 company_cancellationsテーブルを作成中...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_cancellations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                cancellation_reason TEXT,
                cancelled_by TEXT,
                data_deletion_status TEXT DEFAULT 'pending',
                line_account_status TEXT DEFAULT 'active',
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        ''')
    
    # 7. 企業ユーザー管理テーブル
    if 'company_users' in tables_to_create:
        print(f"📋 company_usersテーブルを作成中...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'user',
                permissions TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(company_id, user_id)
            )
        ''')

def main():
    """メイン処理"""
    print("=== 自動データベース検出・企業管理テーブル作成 ===")
    
    # 利用可能なデータベースを検出
    print(f"\n🔍 利用可能なデータベースを検出中...")
    databases = get_available_databases()
    
    if not databases:
        print(f"❌ 利用可能なデータベースが見つかりませんでした")
        print(f"💡 以下のいずれかの方法でデータベース接続を設定してください:")
        print(f"   1. DATABASE_URL環境変数を設定")
        print(f"   2. ローカルPostgreSQLを起動")
        print(f"   3. SQLiteファイルを作成")
        return False
    
    print(f"\n📋 検出されたデータベース ({len(databases)}件):")
    for i, db in enumerate(databases):
        print(f"  {i+1}. {db['name']}")
        if db['type'] == 'postgresql':
            print(f"     - ホスト: {db['host']}:{db['port']}")
            print(f"     - データベース: {db['database']}")
            print(f"     - ユーザー: {db['user']}")
        else:
            print(f"     - ファイル: {db['database']}")
    
    # 各データベースにテーブルを作成
    success_count = 0
    for db in databases:
        if create_company_tables(db):
            success_count += 1
            print(f"\n✅ {db['name']}に企業管理テーブルが作成されました！")
        else:
            print(f"\n❌ {db['name']}へのテーブル作成に失敗しました")
    
    print(f"\n🎯 結果:")
    print(f"  成功: {success_count}/{len(databases)}")
    
    if success_count > 0:
        print(f"\n🎉 企業管理テーブルの作成が完了しました！")
        print(f"💡 PostgreSQL管理画面で企業管理テーブルを確認してください")
        return True
    else:
        print(f"\n❌ すべてのデータベースでテーブル作成に失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 