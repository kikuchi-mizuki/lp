#!/usr/bin/env python3
"""
古いテーブルをCASCADEで削除して企業ユーザー専用最小限データベースに変更するスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# lpディレクトリをパスに追加
lp_dir = os.path.join(current_dir, 'lp')
if lp_dir not in sys.path:
    sys.path.insert(0, lp_dir)

from lp.utils.db import get_db_connection, get_db_type

load_dotenv()

def cleanup_old_tables_cascade():
    """
    古いテーブルをCASCADEで削除して企業ユーザー専用最小限データベースに変更
    """
    conn = None
    c = None
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを確認
        db_type = get_db_type()
        print(f"📊 データベースタイプ: {db_type}")
        
        # 削除するテーブルリスト（依存関係の順序で並べる）
        tables_to_drop = [
            # 依存関係のあるテーブルを先に削除
            'usage_logs',
            'cancellation_history',
            'subscription_periods',
            'company_users',
            'company_usage_logs',
            'company_payments',
            'company_notifications',
            'company_deployments',
            'company_content_types',
            'company_cancellations',
            'cancellation_schedule',
            'user_states',
            # 最後にusersテーブルを削除
            'users'
        ]
        
        print("🗑️  古いテーブルの削除を開始します（CASCADE）...")
        
        for table_name in tables_to_drop:
            try:
                # テーブルが存在するかチェック
                if db_type == 'postgresql':
                    c.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, (table_name,))
                else:
                    c.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, (table_name,))
                
                table_exists = c.fetchone()
                
                if table_exists and (db_type == 'postgresql' and table_exists[0]) or (db_type == 'sqlite' and table_exists):
                    # CASCADEオプションでテーブルを削除
                    c.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    print(f"✅ {table_name} テーブルを削除しました（CASCADE）")
                else:
                    print(f"ℹ️  {table_name} テーブルは存在しません（スキップ）")
                    
            except Exception as e:
                print(f"❌ {table_name} テーブルの削除中にエラー: {e}")
                continue
        
        # 残すべきテーブルを確認
        print("\n📋 残すべきテーブルを確認します...")
        
        if db_type == 'postgresql':
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        else:
            c.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
            """)
        
        remaining_tables = c.fetchall()
        
        print("📊 残っているテーブル:")
        for table in remaining_tables:
            table_name = table[0] if db_type == 'postgresql' else table[0]
            print(f"  - {table_name}")
        
        # 企業ユーザー専用の最小限テーブルが存在するか確認
        required_tables = ['companies', 'company_line_accounts', 'company_subscriptions']
        missing_tables = []
        
        for required_table in required_tables:
            if db_type == 'postgresql':
                c.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    )
                """, (required_table,))
            else:
                c.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (required_table,))
            
            exists = c.fetchone()
            if not exists or (db_type == 'postgresql' and not exists[0]) or (db_type == 'sqlite' and not exists):
                missing_tables.append(required_table)
        
        if missing_tables:
            print(f"\n⚠️  必要なテーブルが不足しています: {missing_tables}")
            print("データベース初期化を実行してください")
        else:
            print("\n✅ 企業ユーザー専用最小限データベースの準備が完了しました")
        
        conn.commit()
        print("\n🎉 テーブル削除処理が完了しました")
        
    except Exception as e:
        print(f"❌ テーブル削除エラー: {e}")
        if conn:
            conn.rollback()
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

def recreate_minimal_tables():
    """
    企業ユーザー専用の最小限テーブルを再作成
    """
    conn = None
    c = None
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        
        print("🔧 企業ユーザー専用最小限テーブルを再作成します...")
        
        if db_type == 'postgresql':
            # 企業基本情報テーブル（最小限）
            c.execute('''
                DROP TABLE IF EXISTS companies CASCADE;
                CREATE TABLE companies (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 企業LINEアカウントテーブル（最小限）
            c.execute('''
                DROP TABLE IF EXISTS company_line_accounts CASCADE;
                CREATE TABLE company_line_accounts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    line_channel_id VARCHAR(255) NOT NULL,
                    line_channel_access_token VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(company_id, content_type)
                )
            ''')
            
            # 企業サブスクリプション管理テーブル（最小限）
            c.execute('''
                DROP TABLE IF EXISTS company_subscriptions CASCADE;
                CREATE TABLE company_subscriptions (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    subscription_status VARCHAR(50) DEFAULT 'active',
                    current_period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(company_id, content_type)
                )
            ''')
            
            # インデックスの作成（パフォーマンス向上）
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_line_accounts_channel_id 
                ON company_line_accounts(line_channel_id)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_subscriptions_status 
                ON company_subscriptions(subscription_status)
            ''')
            
        else:
            # SQLite用の最小限テーブル
            c.execute('''
                DROP TABLE IF EXISTS companies;
                CREATE TABLE companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            c.execute('''
                DROP TABLE IF EXISTS company_line_accounts;
                CREATE TABLE company_line_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    line_channel_id TEXT NOT NULL,
                    line_channel_access_token TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(company_id, content_type)
                )
            ''')
            
            c.execute('''
                DROP TABLE IF EXISTS company_subscriptions;
                CREATE TABLE company_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    subscription_status TEXT DEFAULT 'active',
                    current_period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(company_id, content_type)
                )
            ''')
        
        conn.commit()
        print("✅ 企業ユーザー専用最小限テーブルの再作成が完了しました")
        
    except Exception as e:
        print(f"❌ テーブル再作成エラー: {e}")
        if conn:
            conn.rollback()
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🧹 企業ユーザー専用最小限データベースへの変更を開始します...")
    
    # 古いテーブルをCASCADEで削除
    cleanup_old_tables_cascade()
    
    # 企業ユーザー専用の最小限テーブルを再作成
    recreate_minimal_tables()
    
    print("\n✨ 処理が完了しました！")
    print("\n📝 次のステップ:")
    print("1. アプリケーションを再起動してデータベース初期化を実行")
    print("2. 新しいAPIエンドポイントをテスト")
    print("3. 企業ユーザー専用機能の動作確認") 