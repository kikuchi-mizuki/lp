#!/usr/bin/env python3
"""
古いテーブルを削除して企業ユーザー専用最小限データベースに変更するスクリプト
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

def cleanup_old_tables():
    """
    古いテーブルを削除して企業ユーザー専用最小限データベースに変更
    """
    conn = None
    c = None
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを確認
        db_type = get_db_type()
        print(f"📊 データベースタイプ: {db_type}")
        
        # 削除するテーブルリスト
        tables_to_drop = [
            # 個人ユーザー関連
            'users',
            'subscription_periods', 
            'user_states',
            
            # 詳細情報関連
            'cancellation_history',
            'cancellation_schedule',
            'company_cancellations',
            'company_content_types',
            'company_deployments',
            'company_notifications',
            'company_payments',
            'company_usage_logs',
            'company_users',
            'usage_logs'
        ]
        
        print("🗑️  古いテーブルの削除を開始します...")
        
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
                    # テーブルを削除
                    c.execute(f"DROP TABLE IF EXISTS {table_name}")
                    print(f"✅ {table_name} テーブルを削除しました")
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

def verify_minimal_database():
    """
    最小限データベースの構造を確認
    """
    conn = None
    c = None
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        
        # 企業基本情報テーブルの構造確認
        print("\n📋 企業基本情報テーブルの構造:")
        if db_type == 'postgresql':
            c.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'companies'
                ORDER BY ordinal_position
            """)
        else:
            c.execute("PRAGMA table_info(companies)")
        
        columns = c.fetchall()
        for column in columns:
            if db_type == 'postgresql':
                print(f"  - {column[0]}: {column[1]} ({'NULL' if column[2] == 'YES' else 'NOT NULL'})")
            else:
                print(f"  - {column[1]}: {column[2]} ({'NULL' if column[3] == 0 else 'NOT NULL'})")
        
        # 企業LINEアカウントテーブルの構造確認
        print("\n📋 企業LINEアカウントテーブルの構造:")
        if db_type == 'postgresql':
            c.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'company_line_accounts'
                ORDER BY ordinal_position
            """)
        else:
            c.execute("PRAGMA table_info(company_line_accounts)")
        
        columns = c.fetchall()
        for column in columns:
            if db_type == 'postgresql':
                print(f"  - {column[0]}: {column[1]} ({'NULL' if column[2] == 'YES' else 'NOT NULL'})")
            else:
                print(f"  - {column[1]}: {column[2]} ({'NULL' if column[3] == 0 else 'NOT NULL'})")
        
        # 企業サブスクリプションテーブルの構造確認
        print("\n📋 企業サブスクリプションテーブルの構造:")
        if db_type == 'postgresql':
            c.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'company_subscriptions'
                ORDER BY ordinal_position
            """)
        else:
            c.execute("PRAGMA table_info(company_subscriptions)")
        
        columns = c.fetchall()
        for column in columns:
            if db_type == 'postgresql':
                print(f"  - {column[0]}: {column[1]} ({'NULL' if column[2] == 'YES' else 'NOT NULL'})")
            else:
                print(f"  - {column[1]}: {column[2]} ({'NULL' if column[3] == 0 else 'NOT NULL'})")
        
    except Exception as e:
        print(f"❌ データベース構造確認エラー: {e}")
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🧹 企業ユーザー専用最小限データベースへの変更を開始します...")
    
    # 古いテーブルを削除
    cleanup_old_tables()
    
    # 最小限データベースの構造を確認
    verify_minimal_database()
    
    print("\n✨ 処理が完了しました！")
    print("\n📝 次のステップ:")
    print("1. アプリケーションを再起動してデータベース初期化を実行")
    print("2. 新しいAPIエンドポイントをテスト")
    print("3. 企業ユーザー専用機能の動作確認") 