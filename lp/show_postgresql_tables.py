#!/usr/bin/env python3
"""
PostgreSQL管理画面用テーブル表示スクリプト
"""

import os
import psycopg2
import sys
from urllib.parse import urlparse

def get_postgresql_connections():
    """利用可能なPostgreSQL接続を取得"""
    connections = []
    
    # 1. 環境変数DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql://'):
        try:
            parsed = urlparse(database_url)
            connections.append({
                'name': '環境変数DATABASE_URL',
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path[1:],
                'user': parsed.username,
                'password': parsed.password,
                'url': database_url
            })
        except Exception as e:
            print(f"⚠️ DATABASE_URL解析エラー: {e}")
    
    # 2. 一般的なローカルPostgreSQL接続設定
    local_configs = [
        {
            'name': 'ローカルPostgreSQL (ai_collections)',
            'host': 'localhost',
            'port': 5432,
            'database': 'ai_collections',
            'user': 'postgres',
            'password': 'password'
        },
        {
            'name': 'ローカルPostgreSQL (postgres)',
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'password'
        },
        {
            'name': 'ローカルPostgreSQL (127.0.0.1)',
            'host': '127.0.0.1',
            'port': 5432,
            'database': 'ai_collections',
            'user': 'postgres',
            'password': 'password'
        },
        {
            'name': 'ローカルPostgreSQL (default)',
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': ''
        }
    ]
    
    for config in local_configs:
        connections.append(config)
    
    return connections

def test_connection(connection_info):
    """接続テスト"""
    try:
        if 'url' in connection_info:
            conn = psycopg2.connect(connection_info['url'])
        else:
            conn = psycopg2.connect(
                host=connection_info['host'],
                database=connection_info['database'],
                user=connection_info['user'],
                password=connection_info['password'],
                port=connection_info['port']
            )
        conn.close()
        return True
    except Exception as e:
        return False

def show_database_info(connection_info):
    """データベース情報を表示"""
    print(f"\n=== {connection_info['name']} ===")
    print(f"接続情報:")
    print(f"  ホスト: {connection_info['host']}:{connection_info['port']}")
    print(f"  データベース: {connection_info['database']}")
    print(f"  ユーザー: {connection_info['user']}")
    
    try:
        if 'url' in connection_info:
            conn = psycopg2.connect(connection_info['url'])
        else:
            conn = psycopg2.connect(
                host=connection_info['host'],
                database=connection_info['database'],
                user=connection_info['user'],
                password=connection_info['password'],
                port=connection_info['port']
            )
        
        c = conn.cursor()
        
        # データベース情報
        c.execute("SELECT current_database(), current_user, version()")
        db_info = c.fetchone()
        print(f"\n✅ 接続成功")
        print(f"  現在のデータベース: {db_info[0]}")
        print(f"  接続ユーザー: {db_info[1]}")
        print(f"  PostgreSQLバージョン: {db_info[2].split()[1]}")
        
        # スキーマ一覧
        c.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name
        """)
        schemas = c.fetchall()
        
        print(f"\n📋 スキーマ一覧 ({len(schemas)}件):")
        for schema in schemas:
            print(f"  - {schema[0]}")
        
        # テーブル一覧（publicスキーマ）
        c.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = c.fetchall()
        
        print(f"\n📋 テーブル一覧 (publicスキーマ) ({len(tables)}件):")
        for table in tables:
            table_type = "VIEW" if table[1] == "VIEW" else "TABLE"
            print(f"  - {table[0]} ({table_type})")
        
        # 企業管理テーブルの詳細
        company_tables = [
            'companies',
            'company_line_accounts', 
            'company_payments',
            'company_contents',
            'company_notifications',
            'company_cancellations',
            'company_users'
        ]
        
        existing_company_tables = [table[0] for table in tables if table[0] in company_tables]
        
        print(f"\n🏢 企業管理テーブル ({len(existing_company_tables)}/7件):")
        for table in company_tables:
            status = "✅" if table in existing_company_tables else "❌"
            print(f"  {status} {table}")
        
        # 企業管理テーブルの詳細情報
        if existing_company_tables:
            print(f"\n📊 企業管理テーブル詳細:")
            for table_name in existing_company_tables:
                print(f"\n  📋 {table_name}:")
                
                # テーブル構造
                c.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                columns = c.fetchall()
                
                print(f"    カラム数: {len(columns)}")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    print(f"      - {col[0]}: {col[1]} {nullable}{default}")
                
                # レコード数
                try:
                    c.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = c.fetchone()[0]
                    print(f"    レコード数: {count}")
                    
                    if count > 0:
                        c.execute(f"SELECT * FROM {table_name} LIMIT 3")
                        records = c.fetchall()
                        print(f"    最新3件:")
                        for record in records:
                            print(f"      - {record}")
                except Exception as e:
                    print(f"    レコード数取得エラー: {e}")
        
        # 外部キー制約
        c.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = 'public'
                AND tc.table_name LIKE 'company%'
            ORDER BY tc.table_name, kcu.column_name
        """)
        foreign_keys = c.fetchall()
        
        if foreign_keys:
            print(f"\n🔗 外部キー制約:")
            for fk in foreign_keys:
                print(f"  - {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        import traceback
        traceback.print_exc()

def create_missing_company_tables(connection_info):
    """不足している企業管理テーブルを作成"""
    print(f"\n🚀 {connection_info['name']}に不足している企業管理テーブルを作成中...")
    
    try:
        if 'url' in connection_info:
            conn = psycopg2.connect(connection_info['url'])
        else:
            conn = psycopg2.connect(
                host=connection_info['host'],
                database=connection_info['database'],
                user=connection_info['user'],
                password=connection_info['password'],
                port=connection_info['port']
            )
        
        c = conn.cursor()
        
        # 既存のテーブルを確認
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        existing_tables = [table[0] for table in c.fetchall()]
        
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
        
        # 作成が必要なテーブル
        tables_to_create = [table for table in company_tables if table not in existing_tables]
        
        if not tables_to_create:
            print(f"✅ すべての企業管理テーブルが既に存在します")
            return True
        
        print(f"📝 作成が必要なテーブル ({len(tables_to_create)}件):")
        for table in tables_to_create:
            print(f"  - {table}")
        
        # テーブル作成
        for table_name in tables_to_create:
            print(f"📋 {table_name}テーブルを作成中...")
            
            if table_name == 'companies':
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
            
            elif table_name == 'company_line_accounts':
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
            
            elif table_name == 'company_payments':
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
            
            elif table_name == 'company_contents':
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
            
            elif table_name == 'company_notifications':
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
            
            elif table_name == 'company_cancellations':
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
            
            elif table_name == 'company_users':
                # usersテーブルが存在するかチェック
                c.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'users'
                    )
                """)
                users_exists = c.fetchone()[0]
                
                if users_exists:
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
                    print(f"⚠️ usersテーブルが存在しないため、company_usersテーブルをスキップ")
        
        conn.commit()
        print(f"✅ 企業管理テーブル作成完了")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン処理"""
    print("=== PostgreSQL管理画面用テーブル表示・作成 ===")
    
    # 利用可能なPostgreSQL接続を取得
    connections = get_postgresql_connections()
    
    print(f"\n🔍 利用可能なPostgreSQL接続 ({len(connections)}件):")
    for i, conn in enumerate(connections):
        print(f"  {i+1}. {conn['name']}")
        print(f"     - {conn['host']}:{conn['port']}/{conn['database']}")
    
    # 各接続の情報を表示
    for connection in connections:
        if test_connection(connection):
            show_database_info(connection)
            
            # 不足しているテーブルを作成するか確認
            response = input(f"\n{connection['name']}に不足している企業管理テーブルを作成しますか？ (y/N): ")
            if response.lower() in ['y', 'yes']:
                create_missing_company_tables(connection)
        else:
            print(f"\n❌ {connection['name']}に接続できません")
    
    print(f"\n🎯 完了")
    print(f"💡 PostgreSQL管理画面で企業管理テーブルを確認してください")

if __name__ == "__main__":
    main() 