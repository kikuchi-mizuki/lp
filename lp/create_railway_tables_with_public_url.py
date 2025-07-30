#!/usr/bin/env python3
"""
Railway DATABASE_PUBLIC_URL使用・企業管理テーブル作成スクリプト
"""

import psycopg2
import sys
import time

def create_company_tables_with_public_url():
    """DATABASE_PUBLIC_URLを使用して企業管理テーブルを作成"""
    print("=== Railway DATABASE_PUBLIC_URL使用・企業管理テーブル作成 ===")
    
    # Railwayの外部接続URL
    database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
    
    try:
        # PostgreSQLに接続
        print(f"🔗 Railway PostgreSQLに接続中...")
        print(f"   ホスト: gondola.proxy.rlwy.net")
        print(f"   ポート: 16797")
        print(f"   データベース: railway")
        
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 接続情報を表示
        c.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
        db_info = c.fetchone()
        print(f"✅ 接続成功！")
        print(f"  データベース: {db_info[0]}")
        print(f"  ユーザー: {db_info[1]}")
        print(f"  サーバー: {db_info[2]}:{db_info[3]}")
        
        # 既存のテーブルを確認
        print(f"\n📋 既存のテーブル確認中...")
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        existing_tables = c.fetchall()
        
        print(f"既存テーブル数: {len(existing_tables)}")
        for table in existing_tables:
            print(f"  - {table[0]}")
        
        # 企業管理テーブルを作成
        print(f"\n🚀 企業管理テーブル作成中...")
        
        # 1. 企業基本情報テーブル
        print("  1. companies テーブル作成中...")
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
        print("  2. company_line_accounts テーブル作成中...")
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
        print("  3. company_payments テーブル作成中...")
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
        print("  4. company_contents テーブル作成中...")
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
        print("  5. company_notifications テーブル作成中...")
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
        print("  6. company_cancellations テーブル作成中...")
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
        
        # 7. 企業ユーザー管理テーブル（usersテーブルが存在する場合のみ）
        print("  7. company_users テーブル作成中...")
        c.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
        """)
        users_table_exists = c.fetchone()[0]
        
        if users_table_exists:
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
            print("    ✅ usersテーブルが存在するため、company_usersテーブルを作成しました")
        else:
            print("    ⚠️  usersテーブルが存在しないため、company_usersテーブルは作成しませんでした")
        
        conn.commit()
        print(f"\n✅ 企業管理テーブル作成完了！")
        
        # 作成後のテーブル一覧を確認
        print(f"\n📋 作成された企業管理テーブル:")
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'company%'
            ORDER BY table_name
        """)
        created_tables = c.fetchall()
        
        for table in created_tables:
            print(f"  ✅ {table[0]}")
        
        # 全テーブル一覧を表示
        print(f"\n📋 データベース内の全テーブル:")
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        all_tables = c.fetchall()
        
        for table in all_tables:
            category = "企業管理テーブル" if table[0].startswith('company') else "その他のテーブル"
            print(f"  - {table[0]} ({category})")
        
        conn.close()
        
        print(f"\n🎉 完了！")
        print(f"💡 PostgreSQL管理画面を更新して企業管理テーブルを確認してください")
        print(f"🔗 接続URL: {database_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン処理"""
    success = create_company_tables_with_public_url()
    
    if success:
        print(f"\n✅ 企業管理テーブルの作成が正常に完了しました！")
        print(f"🎯 次のステップ:")
        print(f"   1. RailwayダッシュボードのPostgreSQL管理画面を開く")
        print(f"   2. Dataタブでテーブル一覧を確認")
        print(f"   3. 企業管理テーブルが表示されていることを確認")
        return True
    else:
        print(f"\n❌ テーブル作成に失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 