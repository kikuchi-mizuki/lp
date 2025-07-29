#!/usr/bin/env python3
import os
import psycopg2
from datetime import datetime

def setup_production_database():
    """本番環境のPostgreSQLをセットアップ"""
    try:
        print("=== 本番環境PostgreSQLセットアップ ===")
        
        # RailwayのPostgreSQL URL（実際の値に置き換えてください）
        # RailwayのWebインターフェースから取得したDATABASE_URLを設定
        production_db_url = os.getenv('RAILWAY_DATABASE_URL')
        
        if not production_db_url:
            print("❌ RAILWAY_DATABASE_URL環境変数が設定されていません")
            print("RailwayのWebインターフェースからDATABASE_URLを取得して設定してください")
            print("例: export RAILWAY_DATABASE_URL='postgresql://username:password@host:port/database'")
            return False
        
        print(f"📊 本番環境PostgreSQLに接続中...")
        conn = psycopg2.connect(production_db_url)
        c = conn.cursor()
        
        # テーブル一覧を確認
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        existing_tables = [row[0] for row in c.fetchall()]
        print(f"📋 既存テーブル: {existing_tables}")
        
        # 必要なテーブルを作成
        required_tables = ['users', 'usage_logs', 'subscription_periods', 'cancellation_history', 'user_states']
        
        for table in required_tables:
            if table not in existing_tables:
                print(f"📋 {table}テーブルを作成中...")
                
                if table == 'users':
                    c.execute('''
                        CREATE TABLE users (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            stripe_customer_id VARCHAR(255),
                            stripe_subscription_id VARCHAR(255),
                            line_user_id VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                
                elif table == 'usage_logs':
                    c.execute('''
                        CREATE TABLE usage_logs (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            content_type VARCHAR(100) NOT NULL,
                            is_free BOOLEAN DEFAULT FALSE,
                            pending_charge BOOLEAN DEFAULT FALSE,
                            stripe_usage_record_id VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        )
                    ''')
                
                elif table == 'subscription_periods':
                    c.execute('''
                        CREATE TABLE subscription_periods (
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
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        )
                    ''')
                
                elif table == 'cancellation_history':
                    c.execute('''
                        CREATE TABLE cancellation_history (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            content_type VARCHAR(100) NOT NULL,
                            cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            restriction_start TIMESTAMP,
                            restriction_end TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        )
                    ''')
                
                elif table == 'user_states':
                    c.execute('''
                        CREATE TABLE user_states (
                            id SERIAL PRIMARY KEY,
                            line_user_id VARCHAR(255) UNIQUE NOT NULL,
                            state VARCHAR(100),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                
                print(f"✅ {table}テーブル作成完了")
            else:
                print(f"ℹ️ {table}テーブルは既に存在します")
        
        # テストユーザーを作成
        print(f"\n👥 テストユーザーを作成中...")
        
        test_email = "test_production@example.com"
        test_line_user_id = "Uproduction123456789"
        test_stripe_subscription_id = "sub_production_test_123"
        test_stripe_customer_id = "cus_production_test_123"
        
        # 既存ユーザーをチェック
        c.execute('SELECT id FROM users WHERE email = %s', (test_email,))
        existing_user = c.fetchone()
        
        if existing_user:
            print(f"ユーザー {test_email} は既に存在します。ID: {existing_user[0]}")
            user_id = existing_user[0]
        else:
            # 新しいユーザーを作成
            c.execute('''
                INSERT INTO users (email, line_user_id, stripe_subscription_id, stripe_customer_id, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (test_email, test_line_user_id, test_stripe_subscription_id, test_stripe_customer_id, datetime.now()))
            
            user_id = c.fetchone()[0]
            print(f"新しいユーザーを作成しました。ID: {user_id}")
        
        # テストコンテンツを追加
        print(f"\n📋 テストコンテンツを追加中...")
        
        test_contents = [
            'AI予定秘書',
            'AI経理秘書', 
            'AIタスクコンシェルジュ'
        ]
        
        for i, content in enumerate(test_contents):
            is_free = (i == 0)  # 1個目は無料
            
            # usage_logsに追加
            c.execute('''
                INSERT INTO usage_logs (user_id, content_type, is_free, created_at)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, content, is_free, datetime.now()))
            
            # subscription_periodsに追加
            c.execute('''
                INSERT INTO subscription_periods 
                (user_id, content_type, stripe_subscription_id, subscription_status, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, content, test_stripe_subscription_id, 'active', datetime.now()))
            
            print(f"✅ {content} を追加しました")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ 本番環境PostgreSQLセットアップ完了")
        print(f"   テストユーザーID: {user_id}")
        print(f"   追加コンテンツ数: {len(test_contents)}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_production_database() 